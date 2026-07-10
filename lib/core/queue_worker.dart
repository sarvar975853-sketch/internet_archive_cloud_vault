import 'dart:async';

class PriorityQueue<T extends Comparable<T>> {
  final List<T> _list = [];
  void add(T item) { _list.add(item); _list.sort(); }
  bool get isNotEmpty => _list.isNotEmpty;
  bool get isEmpty => _list.isEmpty;
  int get length => _list.length;
  T get first => _list.first;
  T removeFirst() => _list.removeAt(0);
  void clear() => _list.clear();
}

enum TaskPriority { high, normal, low }

class Task {
  final String id;
  final String name;
  final TaskPriority priority;
  final Future<dynamic> Function() execute;
  final int maxRetries;
  final double timeoutSeconds;
  int retryCount;
  bool isCancelled;

  Task({
    required this.id,
    required this.name,
    this.priority = TaskPriority.normal,
    required this.execute,
    this.maxRetries = 3,
    this.timeoutSeconds = 300.0,
    this.retryCount = 0,
    this.isCancelled = false,
  });
}

class QueueWorker {
  final _taskQueue = PriorityQueue<_QueueEntry>();
  final _activeTasks = <String, Task>{};
  final StreamController<QueueEvent> _eventController = StreamController<QueueEvent>.broadcast();
  Timer? _processingTimer;
  bool _running = false;
  int _concurrentTasks = 0;
  final int _maxWorkers;
  bool _stopped = false;

  Stream<QueueEvent> get events => _eventController.stream;
  int get activeTaskCount => _activeTasks.length;

  QueueWorker({int? maxWorkers, String Function(String)? onTaskUpdate})
      : _maxWorkers = maxWorkers ?? 6 {
    _running = true;
    _startProcessing();
  }

  void _startProcessing() {
    _processingTimer = Timer.periodic(const Duration(milliseconds: 100), (_) {
      _processQueue();
    });
  }

  void submitTask({
    required String name,
    required Future<dynamic> Function() task,
    TaskPriority priority = TaskPriority.normal,
    int maxRetries = 3,
    double timeoutSeconds = 300.0,
  }) {
    final id = 'task_${DateTime.now().millisecondsSinceEpoch}_${_taskQueue.length}';
    final t = Task(
      id: id,
      name: name,
      priority: priority,
      execute: task,
      maxRetries: maxRetries,
      timeoutSeconds: timeoutSeconds,
    );

    final priorityValue = priority == TaskPriority.high
        ? 0
        : priority == TaskPriority.normal ? 1 : 2;

    _taskQueue.add(_QueueEntry(priorityValue, DateTime.now().millisecondsSinceEpoch, t));
    _eventController.add(QueueEvent(QueueEventType.submitted, t));
  }

  void _processQueue() {
    while (_running && _concurrentTasks < _maxWorkers && _taskQueue.isNotEmpty) {
      final entry = _taskQueue.removeFirst();
      final task = entry.task;
      if (task.isCancelled) continue;

      _activeTasks[task.id] = task;
      _concurrentTasks++;
      _executeTask(task);
    }
  }

  Future<void> _executeTask(Task task) async {
    try {
      _eventController.add(QueueEvent(QueueEventType.started, task));
      
      final result = await task.execute().timeout(
        Duration(milliseconds: (task.timeoutSeconds * 1000).toInt()),
      );
      
      if (!task.isCancelled) {
        task.retryCount = 0;
        _eventController.add(QueueEvent(QueueEventType.completed, task, result: result));
      }
    } on TimeoutException {
      if (!_stopped && !task.isCancelled && task.retryCount < task.maxRetries) {
        task.retryCount++;
        await Future<void>.delayed(Duration(seconds: task.retryCount * 2));
        _taskQueue.add(_QueueEntry(
          task.priority == TaskPriority.high ? 0 : task.priority == TaskPriority.normal ? 1 : 2,
          DateTime.now().millisecondsSinceEpoch,
          task,
        ));
        _eventController.add(QueueEvent(QueueEventType.retrying, task));
      } else {
        _eventController.add(QueueEvent(QueueEventType.error, task,
            error: 'Task timed out after ${task.timeoutSeconds}s'));
      }
    } catch (e) {
      if (!_stopped && !task.isCancelled && task.retryCount < task.maxRetries) {
        task.retryCount++;
        await Future<void>.delayed(Duration(seconds: task.retryCount * 2));
        _taskQueue.add(_QueueEntry(
          task.priority == TaskPriority.high ? 0 : task.priority == TaskPriority.normal ? 1 : 2,
          DateTime.now().millisecondsSinceEpoch,
          task,
        ));
        _eventController.add(QueueEvent(QueueEventType.retrying, task));
      } else {
        _eventController.add(QueueEvent(QueueEventType.error, task, error: e.toString()));
      }
    } finally {
      _activeTasks.remove(task.id);
      _concurrentTasks--;
    }
  }

  Future<void> waitForCompletion({Duration? timeout}) async {
    final completer = Completer<void>();
    
    void checkDone() {
      if (_taskQueue.isEmpty && _activeTasks.isEmpty) {
        completer.complete();
      }
    }

    final sub = _eventController.stream.listen((_) => checkDone());
    checkDone();

    if (timeout != null) {
      Future<void>.delayed(timeout, () {
        if (!completer.isCompleted) completer.complete();
      });
    }

    await completer.future;
    sub.cancel();
  }

  void stop() {
    _stopped = true;
    _running = false;
    _processingTimer?.cancel();
    _taskQueue.clear();
    _activeTasks.clear();
    _eventController.close();
  }
}

class _QueueEntry implements Comparable<_QueueEntry> {
  final int priority;
  final int timestamp;
  final Task task;

  _QueueEntry(this.priority, this.timestamp, this.task);

  @override
  int compareTo(_QueueEntry other) {
    final cmp = priority.compareTo(other.priority);
    if (cmp != 0) return cmp;
    return timestamp.compareTo(other.timestamp);
  }
}

enum QueueEventType { submitted, started, completed, error, retrying }

class QueueEvent {
  final QueueEventType type;
  final Task task;
  final dynamic result;
  final String? error;

  QueueEvent(this.type, this.task, {this.result, this.error});
}
