enum TaskPriority { high, normal, low }

enum TaskStatus { pending, running, completed, failed, cancelled }

class QueueTask {
  final String id;
  final String name;
  final TaskPriority priority;
  final TaskStatus status;
  final double progress;
  final String? error;
  final DateTime createdAt;
  final DateTime? completedAt;

  QueueTask({
    required this.id,
    required this.name,
    this.priority = TaskPriority.normal,
    this.status = TaskStatus.pending,
    this.progress = 0.0,
    this.error,
    DateTime? createdAt,
    this.completedAt,
  }) : createdAt = createdAt ?? DateTime.now();

  QueueTask copyWith({
    TaskPriority? priority,
    TaskStatus? status,
    double? progress,
    String? error,
    DateTime? completedAt,
  }) {
    return QueueTask(
      id: id,
      name: name,
      priority: priority ?? this.priority,
      status: status ?? this.status,
      progress: progress ?? this.progress,
      error: error ?? this.error,
      createdAt: createdAt,
      completedAt: completedAt ?? this.completedAt,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'priority': priority.name,
    'status': status.name,
    'progress': progress,
    'error': error,
    'createdAt': createdAt.toIso8601String(),
    'completedAt': completedAt?.toIso8601String(),
  };
}
