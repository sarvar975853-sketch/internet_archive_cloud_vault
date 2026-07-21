import threading
import queue
import time
from typing import Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass
from enum import Enum
from aegis_vault.utils.logger import logger

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 3
    NORMAL = 2
    HIGH = 1

@dataclass
class Task:
    """Represents a task in the queue"""
    func: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority = TaskPriority.NORMAL
    retries: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    task_name: str = ""
    
    def __lt__(self, other):
        """Compare tasks by priority"""
        return self.priority.value < other.priority.value

class QueueWorker:
    """
    Enhanced multi-threaded queue worker with concurrent task processing.
    Features:
    - Multi-threaded uploads and downloads (up to max_workers threads)
    - Task prioritization (HIGH, NORMAL, LOW)
    - Automatic retry logic for failed tasks
    - Task timeout support
    - Progress tracking for long-running tasks
    """
    
    def __init__(self, update_callback: Callable, max_workers: int = 6):
        self.task_queue = queue.PriorityQueue()
        self.running = True
        self.update_callback = update_callback
        self.max_workers = max_workers
        
        # Use ThreadPoolExecutor for concurrent task execution
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="AegisWorker"
        )
        
        # Track active tasks
        self.active_tasks = {}
        self.lock = threading.Lock()
        
        # Start worker thread
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
        
        logger.info(f"✓ QueueWorker initialized with {max_workers} concurrent worker threads")
        
    def submit_task(self, task_func: Callable, *args, priority: TaskPriority = TaskPriority.NORMAL, 
                   max_retries: int = 3, timeout: Optional[float] = None, **kwargs):
        """
        Submit a task to the background queue.
        
        Args:
            task_func: Function to execute
            *args: Positional arguments for the function
            priority: Task priority (HIGH, NORMAL, LOW)
            max_retries: Maximum number of retry attempts
            timeout: Task timeout in seconds
            **kwargs: Keyword arguments for the function
        """
        task = Task(
            func=task_func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout,
            task_name=getattr(task_func, '__name__', 'unknown')
        )
        
        self.task_queue.put((priority.value, time.time(), task))
        queue_size = self.task_queue.qsize()
        logger.info(f"✓ Task submitted: {task.task_name} (Priority: {priority.name}, Queue size: {queue_size})")
        
    def _worker_loop(self):
        """Main worker loop that processes tasks from the queue."""
        while self.running:
            try:
                _, _, task = self.task_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            
            try:
                # Track task
                with self.lock:
                    self.active_tasks[task.task_name] = True
                
                # Execute task with timeout
                self.executor.submit(self._execute_task_with_retry, task)
                
            except Exception as e:
                logger.error(f"Error submitting task: {e}")
            finally:
                self.task_queue.task_done()
    
    def _execute_task_with_retry(self, task: Task):
        """Execute a task with retry logic"""
        attempt = 0
        last_error = None
        
        while attempt <= task.max_retries:
            try:
                # Execute task
                logger.info(f"Executing: {task.task_name} (Attempt {attempt + 1}/{task.max_retries + 1})")
                
                # Use timeout if specified
                if task.timeout:
                    result = self._execute_with_timeout(task.func, task.args, task.kwargs, task.timeout)
                else:
                    result = task.func(*task.args, **task.kwargs)
                
                # Success - notify callback
                if self.update_callback:
                    self.update_callback(task.task_name, "success", result)
                
                logger.info(f"✓ Task completed: {task.task_name}")
                return
                
            except Exception as e:
                last_error = e
                attempt += 1
                
                if attempt <= task.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Task {task.task_name} failed: {e}. Retrying in {wait_time}s... ({attempt}/{task.max_retries})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Task {task.task_name} failed after {task.max_retries + 1} attempts: {last_error}")
                    if self.update_callback:
                        self.update_callback(task.task_name, "error", str(last_error))
            
            finally:
                if attempt > task.max_retries:
                    with self.lock:
                        self.active_tasks.pop(task.task_name, None)
    
    def _execute_with_timeout(self, func: Callable, args: tuple, kwargs: dict, timeout: float) -> Any:
        """Execute function with timeout"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Task execution exceeded {timeout} seconds")
        
        # Set timeout signal (works on Unix-like systems)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout))
            result = func(*args, **kwargs)
            signal.alarm(0)  # Disable alarm
            return result
        except Exception as e:
            signal.alarm(0)  # Disable alarm on error
            raise e
    
    def get_active_task_count(self) -> int:
        """Get count of currently active tasks"""
        with self.lock:
            return len(self.active_tasks)
    
    def wait_for_completion(self, timeout: Optional[float] = None):
        """Wait for all tasks to complete"""
        logger.info("Waiting for all tasks to complete...")
        self.task_queue.join()
        logger.info("✓ All tasks completed")
    
    def stop(self):
        """Gracefully shut down the worker and thread pool"""
        logger.info("Stopping QueueWorker...")
        self.running = False

        # Wait briefly for the worker thread to notice the stop signal
        self.thread.join(timeout=1.0)

        # Don't block on running tasks — they're daemon threads and will die with the process
        self.executor.shutdown(wait=False, cancel_futures=True)
        logger.info("✓ QueueWorker stopped")
