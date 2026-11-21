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
import 'package:serverpod_client/serverpod_client.dart' as _isc;

abstract class RoomMessage
    implements _isc.SerializableModel, _isc.ProtocolSerialization {
  RoomMessage._({
    this.id,
    required this.roomId,
    required this.userIdentifier,
    required this.authorName,
    required this.content,
    required this.createdAt,
  });

  factory RoomMessage({
    int? id,
    required int roomId,
    required String userIdentifier,
    required String authorName,
    required String content,
    required DateTime createdAt,
  }) = _RoomMessageImpl;

  factory RoomMessage.fromJson(Map<String, dynamic> jsonSerialization) {
    return RoomMessage(
      id: jsonSerialization['id'] as int?,
      roomId: jsonSerialization['roomId'] as int,
      userIdentifier: jsonSerialization['userIdentifier'] as String,
      authorName: jsonSerialization['authorName'] as String,
      content: jsonSerialization['content'] as String,
      createdAt: _isc.DateTimeJsonExtension.fromJson(
        jsonSerialization['createdAt'],
      ),
    );
  }

  /// The database id, set if the object has been inserted into the
  /// database or if it has been fetched from the database. Otherwise,
  /// the id will be null.
  int? id;

  int roomId;

  String userIdentifier;

  String authorName;

  String content;

  DateTime createdAt;

  /// Returns a shallow copy of this [RoomMessage]
  /// with some or all fields replaced by the given arguments.
  @_isc.useResult
  RoomMessage copyWith({
    int? id,
    int? roomId,
    String? userIdentifier,
    String? authorName,
    String? content,
    DateTime? createdAt,
  });
  @override
  Map<String, dynamic> toJson() {
    return {
      '__className__': 'RoomMessage',
      if (id != null) 'id': id,
      'roomId': roomId,
      'userIdentifier': userIdentifier,
      'authorName': authorName,
      'content': content,
      'createdAt': createdAt.toJson(),
    };
  }

  @override
  Map<String, dynamic> toJsonForProtocol() {
    return {
      '__className__': 'RoomMessage',
      if (id != null) 'id': id,
      'roomId': roomId,
      'userIdentifier': userIdentifier,
      'authorName': authorName,
      'content': content,
      'createdAt': createdAt.toJson(),
    };
  }

  @override
  String toString() {
    return _isc.SerializationManager.encode(this);
  }
}

class _Undefined {}

class _RoomMessageImpl extends RoomMessage {
  _RoomMessageImpl({
    int? id,
    required int roomId,
    required String userIdentifier,
    required String authorName,
    required String content,
    required DateTime createdAt,
  }) : super._(
         id: id,
         roomId: roomId,
         userIdentifier: userIdentifier,
         authorName: authorName,
         content: content,
         createdAt: createdAt,
       );

  /// Returns a shallow copy of this [RoomMessage]
  /// with some or all fields replaced by the given arguments.
  @_isc.useResult
  @override
  RoomMessage copyWith({
    Object? id = _Undefined,
    int? roomId,
    String? userIdentifier,
    String? authorName,
    String? content,
    DateTime? createdAt,
  }) {
    return RoomMessage(
      id: id is int? ? id : this.id,
      roomId: roomId ?? this.roomId,
      userIdentifier: userIdentifier ?? this.userIdentifier,
      authorName: authorName ?? this.authorName,
      content: content ?? this.content,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
