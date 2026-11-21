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

abstract class RoomParticipant
    implements _is.TableRow<int?>, _is.ProtocolSerialization {
  RoomParticipant._({
    this.id,
    required this.roomId,
    required this.userIdentifier,
    required this.displayName,
    required this.joinedAt,
    required this.lastSeenAt,
  });

  factory RoomParticipant({
    int? id,
    required int roomId,
    required String userIdentifier,
    required String displayName,
    required DateTime joinedAt,
    required DateTime lastSeenAt,
  }) = _RoomParticipantImpl;

  factory RoomParticipant.fromJson(Map<String, dynamic> jsonSerialization) {
    return RoomParticipant(
      id: jsonSerialization['id'] as int?,
      roomId: jsonSerialization['roomId'] as int,
      userIdentifier: jsonSerialization['userIdentifier'] as String,
      displayName: jsonSerialization['displayName'] as String,
      joinedAt: _is.DateTimeJsonExtension.fromJson(
        jsonSerialization['joinedAt'],
      ),
      lastSeenAt: _is.DateTimeJsonExtension.fromJson(
        jsonSerialization['lastSeenAt'],
      ),
    );
  }

  static final t = RoomParticipantTable();

  static const db = RoomParticipantRepository._();

  @override
  int? id;

  int roomId;

  String userIdentifier;

  String displayName;

  DateTime joinedAt;

  DateTime lastSeenAt;

  @override
  _is.Table<int?> get table => t;

  /// Returns a shallow copy of this [RoomParticipant]
  /// with some or all fields replaced by the given arguments.
  @_is.useResult
  RoomParticipant copyWith({
    int? id,
    int? roomId,
    String? userIdentifier,
    String? displayName,
    DateTime? joinedAt,
    DateTime? lastSeenAt,
  });
  @override
  Map<String, dynamic> toJson() {
    return {
      '__className__': 'RoomParticipant',
      if (id != null) 'id': id,
      'roomId': roomId,
      'userIdentifier': userIdentifier,
      'displayName': displayName,
      'joinedAt': joinedAt.toJson(),
      'lastSeenAt': lastSeenAt.toJson(),
    };
  }

  @override
  Map<String, dynamic> toJsonForProtocol() {
    return {
      '__className__': 'RoomParticipant',
      if (id != null) 'id': id,
      'roomId': roomId,
      'userIdentifier': userIdentifier,
      'displayName': displayName,
      'joinedAt': joinedAt.toJson(),
      'lastSeenAt': lastSeenAt.toJson(),
    };
  }

  static RoomParticipantInclude include() {
    return RoomParticipantInclude._();
  }

  static RoomParticipantIncludeList includeList({
    _is.WhereExpressionBuilder<RoomParticipantTable>? where,
    int? limit,
    int? offset,
    _is.OrderByBuilder<RoomParticipantTable>? orderBy,
    _is.OrderByListBuilder<RoomParticipantTable>? orderByList,
    RoomParticipantInclude? include,
  }) {
    return RoomParticipantIncludeList._(
      where: where,
      limit: limit,
      offset: offset,
      orderBy: orderBy?.call(RoomParticipant.t),
      orderByList: orderByList?.call(RoomParticipant.t),
      include: include,
    );
  }

  @override
  String toString() {
    return _is.SerializationManager.encode(this);
  }
}

class _Undefined {}

class _RoomParticipantImpl extends RoomParticipant {
  _RoomParticipantImpl({
    int? id,
    required int roomId,
    required String userIdentifier,
    required String displayName,
    required DateTime joinedAt,
    required DateTime lastSeenAt,
  }) : super._(
         id: id,
         roomId: roomId,
         userIdentifier: userIdentifier,
         displayName: displayName,
         joinedAt: joinedAt,
         lastSeenAt: lastSeenAt,
       );

  /// Returns a shallow copy of this [RoomParticipant]
  /// with some or all fields replaced by the given arguments.
  @_is.useResult
  @override
  RoomParticipant copyWith({
    Object? id = _Undefined,
    int? roomId,
    String? userIdentifier,
    String? displayName,
    DateTime? joinedAt,
    DateTime? lastSeenAt,
  }) {
    return RoomParticipant(
      id: id is int? ? id : this.id,
      roomId: roomId ?? this.roomId,
      userIdentifier: userIdentifier ?? this.userIdentifier,
      displayName: displayName ?? this.displayName,
      joinedAt: joinedAt ?? this.joinedAt,
      lastSeenAt: lastSeenAt ?? this.lastSeenAt,
    );
  }
}

class RoomParticipantUpdateTable extends _is.UpdateTable<RoomParticipantTable> {
  RoomParticipantUpdateTable(super.table);

  _is.ColumnValue<int, int> roomId(int value) => _is.ColumnValue(
    table.roomId,
    value,
  );

  _is.ColumnValue<String, String> userIdentifier(String value) =>
      _is.ColumnValue(
        table.userIdentifier,
        value,
      );

  _is.ColumnValue<String, String> displayName(String value) => _is.ColumnValue(
    table.displayName,
    value,
  );

  _is.ColumnValue<DateTime, DateTime> joinedAt(DateTime value) =>
      _is.ColumnValue(
        table.joinedAt,
        value,
      );

  _is.ColumnValue<DateTime, DateTime> lastSeenAt(DateTime value) =>
      _is.ColumnValue(
        table.lastSeenAt,
        value,
      );
}

class RoomParticipantTable extends _is.Table<int?> {
  RoomParticipantTable({super.tableRelation})
    : super(tableName: 'room_participant') {
    updateTable = RoomParticipantUpdateTable(this);
    roomId = _is.ColumnInt(
      'roomId',
      this,
    );
    userIdentifier = _is.ColumnString(
      'userIdentifier',
      this,
    );
    displayName = _is.ColumnString(
      'displayName',
      this,
    );
    joinedAt = _is.ColumnDateTime(
      'joinedAt',
      this,
    );
    lastSeenAt = _is.ColumnDateTime(
      'lastSeenAt',
      this,
    );
  }

  late final RoomParticipantUpdateTable updateTable;

  late final _is.ColumnInt roomId;

  late final _is.ColumnString userIdentifier;

  late final _is.ColumnString displayName;

  late final _is.ColumnDateTime joinedAt;

  late final _is.ColumnDateTime lastSeenAt;

  @override
  List<_is.Column> get columns => [
    id,
    roomId,
    userIdentifier,
    displayName,
    joinedAt,
    lastSeenAt,
  ];
}

class RoomParticipantInclude extends _is.IncludeObject {
  RoomParticipantInclude._();

  @override
  Map<String, _is.Include?> get includes => {};

  @override
  _is.Table<int?> get table => RoomParticipant.t;
}

class RoomParticipantIncludeList extends _is.IncludeList {
  RoomParticipantIncludeList._({
    _is.WhereExpressionBuilder<RoomParticipantTable>? where,
    super.limit,
    super.offset,
    super.orderBy,
    super.orderByList,
    super.include,
  }) {
    super.where = where?.call(RoomParticipant.t);
  }

  @override
  Map<String, _is.Include?> get includes => include?.includes ?? {};

  @override
  _is.Table<int?> get table => RoomParticipant.t;
}

class RoomParticipantRepository {
  const RoomParticipantRepository._();

  /// Returns a list of [RoomParticipant]s matching the given query parameters.
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
  Future<List<RoomParticipant>> find(
    _is.DatabaseSession session, {
    _is.WhereExpressionBuilder<RoomParticipantTable>? where,
    int? limit,
    int? offset,
    _is.OrderByBuilder<RoomParticipantTable>? orderBy,
    _is.OrderByListBuilder<RoomParticipantTable>? orderByList,
    _is.Transaction? transaction,
    _is.LockMode? lockMode,
    _is.LockBehavior? lockBehavior,
  }) async {
    return session.db.find<RoomParticipant>(
      where: where?.call(RoomParticipant.t),
      orderBy: orderBy?.call(RoomParticipant.t),
      orderByList: orderByList?.call(RoomParticipant.t),
      limit: limit,
      offset: offset,
      transaction: transaction,
      lockMode: lockMode,
      lockBehavior: lockBehavior,
    );
  }

  /// Emits [RoomParticipant]s matching the given query parameters every time the
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
  /// to that set. Pass [Table] instances such as `RoomParticipant.t`.
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
  _ida.Stream<List<RoomParticipant>> watch(
    _is.DatabaseSession session, {
    _is.WhereExpressionBuilder<RoomParticipantTable>? where,
    int? limit,
    int? offset,
    _is.OrderByBuilder<RoomParticipantTable>? orderBy,
    _is.OrderByListBuilder<RoomParticipantTable>? orderByList,
    Duration? throttle = const Duration(milliseconds: 30),
    Iterable<_is.Table>? alsoTriggerOnTables,
  }) {
    return session.db.watch<RoomParticipant>(
      where: where?.call(RoomParticipant.t),
      orderBy: orderBy?.call(RoomParticipant.t),
      orderByList: orderByList?.call(RoomParticipant.t),
      limit: limit,
      offset: offset,
      throttle: throttle,
      alsoTriggerOnTables: alsoTriggerOnTables,
    );
  }

  /// Returns the first matching [RoomParticipant] matching the given query parameters.
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
  Future<RoomParticipant?> findFirstRow(
    _is.DatabaseSession session, {
    _is.WhereExpressionBuilder<RoomParticipantTable>? where,
    int? offset,
    _is.OrderByBuilder<RoomParticipantTable>? orderBy,
    _is.OrderByListBuilder<RoomParticipantTable>? orderByList,
    _is.Transaction? transaction,
    _is.LockMode? lockMode,
    _is.LockBehavior? lockBehavior,
  }) async {
    return session.db.findFirstRow<RoomParticipant>(
      where: where?.call(RoomParticipant.t),
      orderBy: orderBy?.call(RoomParticipant.t),
      orderByList: orderByList?.call(RoomParticipant.t),
      offset: offset,
      transaction: transaction,
      lockMode: lockMode,
      lockBehavior: lockBehavior,
    );
  }

  /// Finds a single [RoomParticipant] by its [id] or null if no such row exists.
  Future<RoomParticipant?> findById(
    _is.DatabaseSession session,
    int id, {
    _is.Transaction? transaction,
    _is.LockMode? lockMode,
    _is.LockBehavior? lockBehavior,
  }) async {
    return session.db.findById<RoomParticipant>(
      id,
      transaction: transaction,
      lockMode: lockMode,
      lockBehavior: lockBehavior,
    );
  }

  /// Inserts all [RoomParticipant]s in the list and returns the inserted rows.
  ///
  /// The returned [RoomParticipant]s will have their `id` fields set.
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
  Future<List<RoomParticipant>> insert(
    _is.DatabaseSession session,
    List<RoomParticipant> rows, {
    _is.Transaction? transaction,
    bool ignoreConflicts = false,
    bool noReturn = false,
  }) async {
    return session.db.insert<RoomParticipant>(
      rows,
      transaction: transaction,
      ignoreConflicts: ignoreConflicts,
      noReturn: noReturn,
    );
  }

  /// Inserts a single [RoomParticipant] and returns the inserted row.
  ///
  /// The returned [RoomParticipant] will have its `id` field set.
  Future<RoomParticipant> insertRow(
    _is.DatabaseSession session,
    RoomParticipant row, {
    _is.Transaction? transaction,
  }) async {
    return session.db.insertRow<RoomParticipant>(
      row,
      transaction: transaction,
    );
  }

  /// Upserts all [RoomParticipant]s in the list and returns the resulting rows.
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
  /// The returned [RoomParticipant]s will have their `id` fields set.
  ///
  /// This is an atomic operation, meaning that if one of the rows fails,
  /// none of the rows will be affected.
  ///
  /// If [noReturn] is set to `true`, the resulting rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<RoomParticipant>> upsert(
    _is.DatabaseSession session,
    List<RoomParticipant> rows, {
    required _is.ColumnSelections<RoomParticipantTable> conflictColumns,
    _is.ColumnSelections<RoomParticipantTable>? updateColumns,
    _is.WhereExpressionBuilder<RoomParticipantTable>? updateWhere,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.upsert<RoomParticipant>(
      rows,
      conflictColumns: conflictColumns(RoomParticipant.t),
      updateColumns: updateColumns?.call(RoomParticipant.t),
      updateWhere: updateWhere?.call(RoomParticipant.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Upserts a single [RoomParticipant] and returns the resulting row.
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
  /// The returned [RoomParticipant] will have its `id` field set.
  Future<RoomParticipant?> upsertRow(
    _is.DatabaseSession session,
    RoomParticipant row, {
    required _is.ColumnSelections<RoomParticipantTable> conflictColumns,
    _is.ColumnSelections<RoomParticipantTable>? updateColumns,
    _is.WhereExpressionBuilder<RoomParticipantTable>? updateWhere,
    _is.Transaction? transaction,
  }) async {
    return session.db.upsertRow<RoomParticipant>(
      row,
      conflictColumns: conflictColumns(RoomParticipant.t),
      updateColumns: updateColumns?.call(RoomParticipant.t),
      updateWhere: updateWhere?.call(RoomParticipant.t),
      transaction: transaction,
    );
  }

  /// Updates all [RoomParticipant]s in the list and returns the updated rows. If
  /// [columns] is provided, only those columns will be updated. Defaults to
  /// all columns.
  /// This is an atomic operation, meaning that if one of the rows fails to
  /// update, none of the rows will be updated.
  ///
  /// If [noReturn] is set to `true`, the updated rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<RoomParticipant>> update(
    _is.DatabaseSession session,
    List<RoomParticipant> rows, {
    _is.ColumnSelections<RoomParticipantTable>? columns,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.update<RoomParticipant>(
      rows,
      columns: columns?.call(RoomParticipant.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Updates a single [RoomParticipant]. The row needs to have its id set.
  /// Optionally, a list of [columns] can be provided to only update those
  /// columns. Defaults to all columns.
  Future<RoomParticipant> updateRow(
    _is.DatabaseSession session,
    RoomParticipant row, {
    _is.ColumnSelections<RoomParticipantTable>? columns,
    _is.Transaction? transaction,
  }) async {
    return session.db.updateRow<RoomParticipant>(
      row,
      columns: columns?.call(RoomParticipant.t),
      transaction: transaction,
    );
  }

  /// Updates a single [RoomParticipant] by its [id] with the specified [columnValues].
  /// Returns the updated row or null if no row with the given id exists.
  Future<RoomParticipant?> updateById(
    _is.DatabaseSession session,
    int id, {
    required _is.ColumnValueListBuilder<RoomParticipantUpdateTable>
    columnValues,
    _is.Transaction? transaction,
  }) async {
    return session.db.updateById<RoomParticipant>(
      id,
      columnValues: columnValues(RoomParticipant.t.updateTable),
      transaction: transaction,
    );
  }

  /// Updates all [RoomParticipant]s matching the [where] expression with the specified [columnValues].
  /// Returns the list of updated rows.
  ///
  /// If [noReturn] is set to `true`, the updated rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<RoomParticipant>> updateWhere(
    _is.DatabaseSession session, {
    required _is.ColumnValueListBuilder<RoomParticipantUpdateTable>
    columnValues,
    required _is.WhereExpressionBuilder<RoomParticipantTable> where,
    int? limit,
    int? offset,
    _is.OrderByBuilder<RoomParticipantTable>? orderBy,
    _is.OrderByListBuilder<RoomParticipantTable>? orderByList,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.updateWhere<RoomParticipant>(
      columnValues: columnValues(RoomParticipant.t.updateTable),
      where: where(RoomParticipant.t),
      limit: limit,
      offset: offset,
      orderBy: orderBy?.call(RoomParticipant.t),
      orderByList: orderByList?.call(RoomParticipant.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Deletes all [RoomParticipant]s in the list and returns the deleted rows.
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
  Future<List<RoomParticipant>> delete(
    _is.DatabaseSession session,
    List<RoomParticipant> rows, {
    _is.OrderByBuilder<RoomParticipantTable>? orderBy,
    _is.OrderByListBuilder<RoomParticipantTable>? orderByList,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.delete<RoomParticipant>(
      rows,
      orderBy: orderBy?.call(RoomParticipant.t),
      orderByList: orderByList?.call(RoomParticipant.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Deletes a single [RoomParticipant].
  Future<RoomParticipant> deleteRow(
    _is.DatabaseSession session,
    RoomParticipant row, {
    _is.Transaction? transaction,
  }) async {
    return session.db.deleteRow<RoomParticipant>(
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
  Future<List<RoomParticipant>> deleteWhere(
    _is.DatabaseSession session, {
    required _is.WhereExpressionBuilder<RoomParticipantTable> where,
    _is.OrderByBuilder<RoomParticipantTable>? orderBy,
    _is.OrderByListBuilder<RoomParticipantTable>? orderByList,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.deleteWhere<RoomParticipant>(
      where: where(RoomParticipant.t),
      orderBy: orderBy?.call(RoomParticipant.t),
      orderByList: orderByList?.call(RoomParticipant.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Counts the number of rows matching the [where] expression. If omitted,
  /// will return the count of all rows in the table.
  Future<int> count(
    _is.DatabaseSession session, {
    _is.WhereExpressionBuilder<RoomParticipantTable>? where,
    int? limit,
    _is.Transaction? transaction,
  }) async {
    return session.db.count<RoomParticipant>(
      where: where?.call(RoomParticipant.t),
      limit: limit,
      transaction: transaction,
    );
  }

  /// Acquires row-level locks on [RoomParticipant] rows matching the [where] expression.
  Future<void> lockRows(
    _is.DatabaseSession session, {
    required _is.WhereExpressionBuilder<RoomParticipantTable> where,
    required _is.LockMode lockMode,
    required _is.Transaction transaction,
    _is.LockBehavior lockBehavior = _is.LockBehavior.wait,
  }) async {
    return session.db.lockRows<RoomParticipant>(
      where: where(RoomParticipant.t),
      lockMode: lockMode,
      lockBehavior: lockBehavior,
      transaction: transaction,
    );
  }
}
