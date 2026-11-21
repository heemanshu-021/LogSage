/* AUTOMATICALLY GENERATED CODE DO NOT MODIFY */
/*   To generate run: "serverpod generate"    */

// ignore_for_file: implementation_imports
// ignore_for_file: library_private_types_in_public_api
// ignore_for_file: non_constant_identifier_names
// ignore_for_file: public_member_api_docs
// ignore_for_file: type_literal_in_constant_pattern
// ignore_for_file: use_super_parameters
// ignore_for_file: invalid_use_of_internal_member

// ignore_for_file: no_leading_underscores_for_library_prefixes
import 'dart:async' as _ida;
import 'package:serverpod/serverpod.dart' as _is;

abstract class IncidentWarRoom
    implements _is.TableRow<int?>, _is.ProtocolSerialization {
  IncidentWarRoom._({
    this.id,
    required this.incidentId,
    required this.incidentTitle,
    required this.joinCode,
    required this.createdByUserId,
    required this.createdAt,
    this.closedAt,
  });

  factory IncidentWarRoom({
    int? id,
    required String incidentId,
    required String incidentTitle,
    required String joinCode,
    required String createdByUserId,
    required DateTime createdAt,
    DateTime? closedAt,
  }) = _IncidentWarRoomImpl;

  factory IncidentWarRoom.fromJson(Map<String, dynamic> jsonSerialization) {
    return IncidentWarRoom(
      id: jsonSerialization['id'] as int?,
      incidentId: jsonSerialization['incidentId'] as String,
      incidentTitle: jsonSerialization['incidentTitle'] as String,
      joinCode: jsonSerialization['joinCode'] as String,
      createdByUserId: jsonSerialization['createdByUserId'] as String,
      createdAt: _is.DateTimeJsonExtension.fromJson(
        jsonSerialization['createdAt'],
      ),
      closedAt: jsonSerialization['closedAt'] == null
          ? null
          : _is.DateTimeJsonExtension.fromJson(jsonSerialization['closedAt']),
    );
  }

  static final t = IncidentWarRoomTable();

  static const db = IncidentWarRoomRepository._();

  @override
  int? id;

  String incidentId;

  String incidentTitle;

  String joinCode;

  String createdByUserId;

  DateTime createdAt;

  DateTime? closedAt;

  @override
  _is.Table<int?> get table => t;

  /// Returns a shallow copy of this [IncidentWarRoom]
  /// with some or all fields replaced by the given arguments.
  @_is.useResult
  IncidentWarRoom copyWith({
    int? id,
    String? incidentId,
    String? incidentTitle,
    String? joinCode,
    String? createdByUserId,
    DateTime? createdAt,
    DateTime? closedAt = const _is.$UndefinedDateTime(),
  });
  @override
  Map<String, dynamic> toJson() {
    return {
      '__className__': 'IncidentWarRoom',
      if (id != null) 'id': id,
      'incidentId': incidentId,
      'incidentTitle': incidentTitle,
      'joinCode': joinCode,
      'createdByUserId': createdByUserId,
      'createdAt': createdAt.toJson(),
      if (closedAt != null) 'closedAt': closedAt?.toJson(),
    };
  }

  @override
  Map<String, dynamic> toJsonForProtocol() {
    return {
      '__className__': 'IncidentWarRoom',
      if (id != null) 'id': id,
      'incidentId': incidentId,
      'incidentTitle': incidentTitle,
      'joinCode': joinCode,
      'createdByUserId': createdByUserId,
      'createdAt': createdAt.toJson(),
      if (closedAt != null) 'closedAt': closedAt?.toJson(),
    };
  }

  static IncidentWarRoomInclude include() {
    return IncidentWarRoomInclude._();
  }

  static IncidentWarRoomIncludeList includeList({
    _is.WhereExpressionBuilder<IncidentWarRoomTable>? where,
    int? limit,
    int? offset,
    _is.OrderByBuilder<IncidentWarRoomTable>? orderBy,
    _is.OrderByListBuilder<IncidentWarRoomTable>? orderByList,
    IncidentWarRoomInclude? include,
  }) {
    return IncidentWarRoomIncludeList._(
      where: where,
      limit: limit,
      offset: offset,
      orderBy: orderBy?.call(IncidentWarRoom.t),
      orderByList: orderByList?.call(IncidentWarRoom.t),
      include: include,
    );
  }

  @override
  String toString() {
    return _is.SerializationManager.encode(this);
  }
}

class _Undefined {}

class _IncidentWarRoomImpl extends IncidentWarRoom {
  _IncidentWarRoomImpl({
    int? id,
    required String incidentId,
    required String incidentTitle,
    required String joinCode,
    required String createdByUserId,
    required DateTime createdAt,
    DateTime? closedAt,
  }) : super._(
         id: id,
         incidentId: incidentId,
         incidentTitle: incidentTitle,
         joinCode: joinCode,
         createdByUserId: createdByUserId,
         createdAt: createdAt,
         closedAt: closedAt,
       );

  /// Returns a shallow copy of this [IncidentWarRoom]
  /// with some or all fields replaced by the given arguments.
  @_is.useResult
  @override
  IncidentWarRoom copyWith({
    Object? id = _Undefined,
    String? incidentId,
    String? incidentTitle,
    String? joinCode,
    String? createdByUserId,
    DateTime? createdAt,
    DateTime? closedAt = const _is.$UndefinedDateTime(),
  }) {
    return IncidentWarRoom(
      id: id is int? ? id : this.id,
      incidentId: incidentId ?? this.incidentId,
      incidentTitle: incidentTitle ?? this.incidentTitle,
      joinCode: joinCode ?? this.joinCode,
      createdByUserId: createdByUserId ?? this.createdByUserId,
      createdAt: createdAt ?? this.createdAt,
      closedAt: closedAt is _is.UndefinedSentinel ? this.closedAt : closedAt,
    );
  }
}

class IncidentWarRoomUpdateTable extends _is.UpdateTable<IncidentWarRoomTable> {
  IncidentWarRoomUpdateTable(super.table);

  _is.ColumnValue<String, String> incidentId(String value) => _is.ColumnValue(
    table.incidentId,
    value,
  );

  _is.ColumnValue<String, String> incidentTitle(String value) =>
      _is.ColumnValue(
        table.incidentTitle,
        value,
      );

  _is.ColumnValue<String, String> joinCode(String value) => _is.ColumnValue(
    table.joinCode,
    value,
  );

  _is.ColumnValue<String, String> createdByUserId(String value) =>
      _is.ColumnValue(
        table.createdByUserId,
        value,
      );

  _is.ColumnValue<DateTime, DateTime> createdAt(DateTime value) =>
      _is.ColumnValue(
        table.createdAt,
        value,
      );

  _is.ColumnValue<DateTime, DateTime> closedAt(DateTime? value) =>
      _is.ColumnValue(
        table.closedAt,
        value,
      );
}

class IncidentWarRoomTable extends _is.Table<int?> {
  IncidentWarRoomTable({super.tableRelation})
    : super(tableName: 'incident_war_room') {
    updateTable = IncidentWarRoomUpdateTable(this);
    incidentId = _is.ColumnString(
      'incidentId',
      this,
    );
    incidentTitle = _is.ColumnString(
      'incidentTitle',
      this,
    );
    joinCode = _is.ColumnString(
      'joinCode',
      this,
    );
    createdByUserId = _is.ColumnString(
      'createdByUserId',
      this,
    );
    createdAt = _is.ColumnDateTime(
      'createdAt',
      this,
    );
    closedAt = _is.ColumnDateTime(
      'closedAt',
      this,
    );
  }

  late final IncidentWarRoomUpdateTable updateTable;

  late final _is.ColumnString incidentId;

  late final _is.ColumnString incidentTitle;

  late final _is.ColumnString joinCode;

  late final _is.ColumnString createdByUserId;

  late final _is.ColumnDateTime createdAt;

  late final _is.ColumnDateTime closedAt;

  @override
  List<_is.Column> get columns => [
    id,
    incidentId,
    incidentTitle,
    joinCode,
    createdByUserId,
    createdAt,
    closedAt,
  ];
}

class IncidentWarRoomInclude extends _is.IncludeObject {
  IncidentWarRoomInclude._();

  @override
  Map<String, _is.Include?> get includes => {};

  @override
  _is.Table<int?> get table => IncidentWarRoom.t;
}

class IncidentWarRoomIncludeList extends _is.IncludeList {
  IncidentWarRoomIncludeList._({
    _is.WhereExpressionBuilder<IncidentWarRoomTable>? where,
    super.limit,
    super.offset,
    super.orderBy,
    super.orderByList,
    super.include,
  }) {
    super.where = where?.call(IncidentWarRoom.t);
  }

  @override
  Map<String, _is.Include?> get includes => include?.includes ?? {};

  @override
  _is.Table<int?> get table => IncidentWarRoom.t;
}

class IncidentWarRoomRepository {
  const IncidentWarRoomRepository._();

  /// Returns a list of [IncidentWarRoom]s matching the given query parameters.
  ///
  /// Use [where] to specify which items to include in the return value.
  /// If none is specified, all items will be returned.
  ///
  /// To specify the order of the items use [orderBy] or [orderByList]
  /// when sorting by multiple columns.
  ///
  /// The maximum number of items can be set by [limit]. If no limit is set,
  /// all items matching the query will be returned.
  ///
  /// [offset] defines how many items to skip, after which [limit] (or all)
  /// items are read from the database.
  ///
  /// ```dart
  /// var persons = await Persons.db.find(
  ///   session,
  ///   where: (t) => t.lastName.equals('Jones'),
  ///   orderBy: (t) => t.firstName,
  ///   limit: 100,
  /// );
  /// ```
  Future<List<IncidentWarRoom>> find(
    _is.DatabaseSession session, {
    _is.WhereExpressionBuilder<IncidentWarRoomTable>? where,
    int? limit,
    int? offset,
    _is.OrderByBuilder<IncidentWarRoomTable>? orderBy,
    _is.OrderByListBuilder<IncidentWarRoomTable>? orderByList,
    _is.Transaction? transaction,
    _is.LockMode? lockMode,
    _is.LockBehavior? lockBehavior,
  }) async {
    return session.db.find<IncidentWarRoom>(
      where: where?.call(IncidentWarRoom.t),
      orderBy: orderBy?.call(IncidentWarRoom.t),
      orderByList: orderByList?.call(IncidentWarRoom.t),
      limit: limit,
      offset: offset,
      transaction: transaction,
      lockMode: lockMode,
      lockBehavior: lockBehavior,
    );
  }

  /// Emits [IncidentWarRoom]s matching the given query parameters every time the
  /// source tables are modified.
  ///
  /// Use [where] to specify which items to include in the return value.
  /// If none is specified, all items will be returned.
  ///
  /// To specify the order of the items use [orderBy] or [orderByList]
  /// when sorting by multiple columns.
  ///
  /// The maximum number of items can be set by [limit]. If no limit is set,
  /// all items matching the query will be returned.
  ///
  /// [offset] defines how many items to skip, after which [limit] (or all)
  /// items are read from the database.
  ///
  /// Use [throttle] to specify the minimum interval between queries. It can
  /// also be set to `null`, in which case the stream will only be throttled
  /// when its subscription is paused.
  ///
  /// Source tables are collected from the queried table, [where], [orderBy],
  /// [orderByList], and the [include] graph. [alsoTriggerOnTables] is added
  /// to that set. Pass [Table] instances such as `IncidentWarRoom.t`.
  ///
  /// Raw [Expression] SQL is not inspected. Tables referenced only in raw
  /// SQL must be passed via [alsoTriggerOnTables].
  ///
  /// The stream always reads committed state and never joins an ambient
  /// [Transaction]. Emissions for a write fire after that write commits.
  ///
  /// Currently only supported on SQLite. Calling this method on PostgreSQL
  /// throws an [UnsupportedError].
  ///
  /// ```dart
  /// var subscription = Persons.db.watch(
  ///   session,
  ///   where: (t) => t.lastName.equals('Jones'),
  ///   orderBy: (t) => t.firstName,
  ///   limit: 100,
  /// ).listen((persons) {
  ///   // Handle the latest matching rows.
  /// });
  /// ```
  _ida.Stream<List<IncidentWarRoom>> watch(
    _is.DatabaseSession session, {
    _is.WhereExpressionBuilder<IncidentWarRoomTable>? where,
    int? limit,
    int? offset,
    _is.OrderByBuilder<IncidentWarRoomTable>? orderBy,
    _is.OrderByListBuilder<IncidentWarRoomTable>? orderByList,
    Duration? throttle = const Duration(milliseconds: 30),
    Iterable<_is.Table>? alsoTriggerOnTables,
  }) {
    return session.db.watch<IncidentWarRoom>(
      where: where?.call(IncidentWarRoom.t),
      orderBy: orderBy?.call(IncidentWarRoom.t),
      orderByList: orderByList?.call(IncidentWarRoom.t),
      limit: limit,
      offset: offset,
      throttle: throttle,
      alsoTriggerOnTables: alsoTriggerOnTables,
    );
  }

  /// Returns the first matching [IncidentWarRoom] matching the given query parameters.
  ///
  /// Use [where] to specify which items to include in the return value.
  /// If none is specified, all items will be returned.
  ///
  /// To specify the order use [orderBy] or [orderByList]
  /// when sorting by multiple columns.
  ///
  /// [offset] defines how many items to skip, after which the next one will be picked.
  ///
  /// ```dart
  /// var youngestPerson = await Persons.db.findFirstRow(
  ///   session,
  ///   where: (t) => t.lastName.equals('Jones'),
  ///   orderBy: (t) => t.age,
  /// );
  /// ```
  Future<IncidentWarRoom?> findFirstRow(
    _is.DatabaseSession session, {
    _is.WhereExpressionBuilder<IncidentWarRoomTable>? where,
    int? offset,
    _is.OrderByBuilder<IncidentWarRoomTable>? orderBy,
    _is.OrderByListBuilder<IncidentWarRoomTable>? orderByList,
    _is.Transaction? transaction,
    _is.LockMode? lockMode,
    _is.LockBehavior? lockBehavior,
  }) async {
    return session.db.findFirstRow<IncidentWarRoom>(
      where: where?.call(IncidentWarRoom.t),
      orderBy: orderBy?.call(IncidentWarRoom.t),
      orderByList: orderByList?.call(IncidentWarRoom.t),
      offset: offset,
      transaction: transaction,
      lockMode: lockMode,
      lockBehavior: lockBehavior,
    );
  }

  /// Finds a single [IncidentWarRoom] by its [id] or null if no such row exists.
  Future<IncidentWarRoom?> findById(
    _is.DatabaseSession session,
    int id, {
    _is.Transaction? transaction,
    _is.LockMode? lockMode,
    _is.LockBehavior? lockBehavior,
  }) async {
    return session.db.findById<IncidentWarRoom>(
      id,
      transaction: transaction,
      lockMode: lockMode,
      lockBehavior: lockBehavior,
    );
  }

  /// Inserts all [IncidentWarRoom]s in the list and returns the inserted rows.
  ///
  /// The returned [IncidentWarRoom]s will have their `id` fields set.
  ///
  /// This is an atomic operation, meaning that if one of the rows fails to
  /// insert, none of the rows will be inserted.
  ///
  /// If [ignoreConflicts] is set to `true`, rows that conflict with existing
  /// rows are silently skipped, and only the successfully inserted rows are
  /// returned.
  ///
  /// If [noReturn] is set to `true`, the inserted rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<IncidentWarRoom>> insert(
    _is.DatabaseSession session,
    List<IncidentWarRoom> rows, {
    _is.Transaction? transaction,
    bool ignoreConflicts = false,
    bool noReturn = false,
  }) async {
    return session.db.insert<IncidentWarRoom>(
      rows,
      transaction: transaction,
      ignoreConflicts: ignoreConflicts,
      noReturn: noReturn,
    );
  }

  /// Inserts a single [IncidentWarRoom] and returns the inserted row.
  ///
  /// The returned [IncidentWarRoom] will have its `id` field set.
  Future<IncidentWarRoom> insertRow(
    _is.DatabaseSession session,
    IncidentWarRoom row, {
    _is.Transaction? transaction,
  }) async {
    return session.db.insertRow<IncidentWarRoom>(
      row,
      transaction: transaction,
    );
  }

  /// Upserts all [IncidentWarRoom]s in the list and returns the resulting rows.
  ///
  /// If a row conflicts on the given [conflictColumns], the existing row is
  /// updated with the new values. Otherwise, a new row is inserted.
  ///
  /// If [updateColumns] is provided, only those columns will be updated on
  /// conflict. If null, all non-conflict, non-id columns are updated.
  ///
  /// If [updateWhere] is provided, the update only applies to rows matching the
  /// given expression. Conflicting rows that don't match are skipped and not
  /// returned, so the resulting list may be shorter than [rows].
  ///
  /// The returned [IncidentWarRoom]s will have their `id` fields set.
  ///
  /// This is an atomic operation, meaning that if one of the rows fails,
  /// none of the rows will be affected.
  ///
  /// If [noReturn] is set to `true`, the resulting rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<IncidentWarRoom>> upsert(
    _is.DatabaseSession session,
    List<IncidentWarRoom> rows, {
    required _is.ColumnSelections<IncidentWarRoomTable> conflictColumns,
    _is.ColumnSelections<IncidentWarRoomTable>? updateColumns,
    _is.WhereExpressionBuilder<IncidentWarRoomTable>? updateWhere,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.upsert<IncidentWarRoom>(
      rows,
      conflictColumns: conflictColumns(IncidentWarRoom.t),
      updateColumns: updateColumns?.call(IncidentWarRoom.t),
      updateWhere: updateWhere?.call(IncidentWarRoom.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Upserts a single [IncidentWarRoom] and returns the resulting row.
  ///
  /// If the row conflicts on the given [conflictColumns], the existing row is
  /// updated. Otherwise, a new row is inserted.
  ///
  /// If [updateColumns] is provided, only those columns will be updated on
  /// conflict. If null, all non-conflict, non-id columns are updated.
  ///
  /// If [updateWhere] is provided, the update only applies when the existing
  /// row matches the expression. Returns `null` if no row was affected — for
  /// example when [updateWhere] does not match the conflicting row.
  ///
  /// The returned [IncidentWarRoom] will have its `id` field set.
  Future<IncidentWarRoom?> upsertRow(
    _is.DatabaseSession session,
    IncidentWarRoom row, {
    required _is.ColumnSelections<IncidentWarRoomTable> conflictColumns,
    _is.ColumnSelections<IncidentWarRoomTable>? updateColumns,
    _is.WhereExpressionBuilder<IncidentWarRoomTable>? updateWhere,
    _is.Transaction? transaction,
  }) async {
    return session.db.upsertRow<IncidentWarRoom>(
      row,
      conflictColumns: conflictColumns(IncidentWarRoom.t),
      updateColumns: updateColumns?.call(IncidentWarRoom.t),
      updateWhere: updateWhere?.call(IncidentWarRoom.t),
      transaction: transaction,
    );
  }

  /// Updates all [IncidentWarRoom]s in the list and returns the updated rows. If
  /// [columns] is provided, only those columns will be updated. Defaults to
  /// all columns.
  /// This is an atomic operation, meaning that if one of the rows fails to
  /// update, none of the rows will be updated.
  ///
  /// If [noReturn] is set to `true`, the updated rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<IncidentWarRoom>> update(
    _is.DatabaseSession session,
    List<IncidentWarRoom> rows, {
    _is.ColumnSelections<IncidentWarRoomTable>? columns,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.update<IncidentWarRoom>(
      rows,
      columns: columns?.call(IncidentWarRoom.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Updates a single [IncidentWarRoom]. The row needs to have its id set.
  /// Optionally, a list of [columns] can be provided to only update those
  /// columns. Defaults to all columns.
  Future<IncidentWarRoom> updateRow(
    _is.DatabaseSession session,
    IncidentWarRoom row, {
    _is.ColumnSelections<IncidentWarRoomTable>? columns,
    _is.Transaction? transaction,
  }) async {
    return session.db.updateRow<IncidentWarRoom>(
      row,
      columns: columns?.call(IncidentWarRoom.t),
      transaction: transaction,
    );
  }

  /// Updates a single [IncidentWarRoom] by its [id] with the specified [columnValues].
  /// Returns the updated row or null if no row with the given id exists.
  Future<IncidentWarRoom?> updateById(
    _is.DatabaseSession session,
    int id, {
    required _is.ColumnValueListBuilder<IncidentWarRoomUpdateTable>
    columnValues,
    _is.Transaction? transaction,
  }) async {
    return session.db.updateById<IncidentWarRoom>(
      id,
      columnValues: columnValues(IncidentWarRoom.t.updateTable),
      transaction: transaction,
    );
  }

  /// Updates all [IncidentWarRoom]s matching the [where] expression with the specified [columnValues].
  /// Returns the list of updated rows.
  ///
  /// If [noReturn] is set to `true`, the updated rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<IncidentWarRoom>> updateWhere(
    _is.DatabaseSession session, {
    required _is.ColumnValueListBuilder<IncidentWarRoomUpdateTable>
    columnValues,
    required _is.WhereExpressionBuilder<IncidentWarRoomTable> where,
    int? limit,
    int? offset,
    _is.OrderByBuilder<IncidentWarRoomTable>? orderBy,
    _is.OrderByListBuilder<IncidentWarRoomTable>? orderByList,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.updateWhere<IncidentWarRoom>(
      columnValues: columnValues(IncidentWarRoom.t.updateTable),
      where: where(IncidentWarRoom.t),
      limit: limit,
      offset: offset,
      orderBy: orderBy?.call(IncidentWarRoom.t),
      orderByList: orderByList?.call(IncidentWarRoom.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Deletes all [IncidentWarRoom]s in the list and returns the deleted rows.
  ///
  /// To specify the order of the returned rows use [orderBy] or [orderByList]
  /// when sorting by multiple columns.
  ///
  /// This is an atomic operation, meaning that if one of the rows fail to
  /// be deleted, none of the rows will be deleted.
  ///
  /// If [noReturn] is set to `true`, the deleted rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<IncidentWarRoom>> delete(
    _is.DatabaseSession session,
    List<IncidentWarRoom> rows, {
    _is.OrderByBuilder<IncidentWarRoomTable>? orderBy,
    _is.OrderByListBuilder<IncidentWarRoomTable>? orderByList,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.delete<IncidentWarRoom>(
      rows,
      orderBy: orderBy?.call(IncidentWarRoom.t),
      orderByList: orderByList?.call(IncidentWarRoom.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Deletes a single [IncidentWarRoom].
  Future<IncidentWarRoom> deleteRow(
    _is.DatabaseSession session,
    IncidentWarRoom row, {
    _is.Transaction? transaction,
  }) async {
    return session.db.deleteRow<IncidentWarRoom>(
      row,
      transaction: transaction,
    );
  }

  /// Deletes all rows matching the [where] expression.
  ///
  /// To specify the order of the returned rows use [orderBy] or [orderByList]
  /// when sorting by multiple columns.
  ///
  /// If [noReturn] is set to `true`, the deleted rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<IncidentWarRoom>> deleteWhere(
    _is.DatabaseSession session, {
    required _is.WhereExpressionBuilder<IncidentWarRoomTable> where,
    _is.OrderByBuilder<IncidentWarRoomTable>? orderBy,
    _is.OrderByListBuilder<IncidentWarRoomTable>? orderByList,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.deleteWhere<IncidentWarRoom>(
      where: where(IncidentWarRoom.t),
      orderBy: orderBy?.call(IncidentWarRoom.t),
      orderByList: orderByList?.call(IncidentWarRoom.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Counts the number of rows matching the [where] expression. If omitted,
  /// will return the count of all rows in the table.
  Future<int> count(
    _is.DatabaseSession session, {
    _is.WhereExpressionBuilder<IncidentWarRoomTable>? where,
    int? limit,
    _is.Transaction? transaction,
  }) async {
    return session.db.count<IncidentWarRoom>(
      where: where?.call(IncidentWarRoom.t),
      limit: limit,
      transaction: transaction,
    );
  }

  /// Acquires row-level locks on [IncidentWarRoom] rows matching the [where] expression.
  Future<void> lockRows(
    _is.DatabaseSession session, {
    required _is.WhereExpressionBuilder<IncidentWarRoomTable> where,
    required _is.LockMode lockMode,
    required _is.Transaction transaction,
    _is.LockBehavior lockBehavior = _is.LockBehavior.wait,
  }) async {
    return session.db.lockRows<IncidentWarRoom>(
      where: where(IncidentWarRoom.t),
      lockMode: lockMode,
      lockBehavior: lockBehavior,
      transaction: transaction,
    );
  }
}
