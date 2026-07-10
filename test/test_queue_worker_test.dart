import 'package:flutter_test/flutter_test.dart';
import 'package:aegis_vault/core/queue_worker.dart';

void main() {
  group('QueueWorker', () {
    test('submit and execute task', () async {
      final worker = QueueWorker(maxWorkers: 1);
      bool executed = false;
      worker.submitTask(
        name: 'test',
        task: () async {
          executed = true;
          return 'done';
        },
      );
      await Future.delayed(const Duration(milliseconds: 500));
      expect(executed, isTrue);
      worker.stop();
    });

    test('priority order (high before low)', () async {
      final worker = QueueWorker(maxWorkers: 1);
      final order = <int>[];
      worker.submitTask(name: 'low', task: () async {
        await Future.delayed(const Duration(milliseconds: 50));
        order.add(2);
        return null;
      }, priority: TaskPriority.low);
      worker.submitTask(name: 'high', task: () async {
        order.add(1);
        return null;
      }, priority: TaskPriority.high);
      await Future.delayed(const Duration(milliseconds: 500));
      expect(order, [1, 2]);
      worker.stop();
    });

    test('retry on failure', () async {
      final worker = QueueWorker(maxWorkers: 1);
      int attempts = 0;
      worker.submitTask(
        name: 'retry_test',
        task: () async {
          attempts++;
          if (attempts < 2) throw Exception('fail');
          return 'success';
        },
        maxRetries: 2,
      );
      await Future.delayed(const Duration(milliseconds: 800));
      expect(attempts, 2);
      worker.stop();
    });

    test('exhaust retries and report error', () async {
      final worker = QueueWorker(maxWorkers: 1);
      String? lastEvent;
      worker.events.listen((event) {
        if (event.type == QueueEventType.error) {
          lastEvent = 'error';
        }
      });
      worker.submitTask(
        name: 'fail_all',
        task: () async => throw Exception('always fails'),
        maxRetries: 1,
      );
      await Future.delayed(const Duration(seconds: 2));
      expect(lastEvent, 'error');
      worker.stop();
    });

    test('active task count', () async {
      final worker = QueueWorker(maxWorkers: 2);
      expect(worker.activeTaskCount, 0);
      worker.submitTask(name: 't1', task: () async {
        await Future.delayed(const Duration(seconds: 1));
        return null;
      });
      worker.submitTask(name: 't2', task: () async {
        await Future.delayed(const Duration(seconds: 1));
        return null;
      });
      await Future.delayed(const Duration(milliseconds: 200));
      expect(worker.activeTaskCount, greaterThan(0));
      await Future.delayed(const Duration(seconds: 2));
      worker.stop();
    });

    test('stop worker', () async {
      final worker = QueueWorker(maxWorkers: 1);
      bool executed = false;
      worker.submitTask(name: 'late', task: () async {
        executed = true;
        return null;
      });
      worker.stop();
      await Future.delayed(const Duration(milliseconds: 200));
      // May or may not have executed, but shouldn't crash
      worker.stop();
    });
  });
}
