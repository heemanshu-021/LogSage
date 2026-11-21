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
import 'package:serverpod/serverpod.dart' as _is;

abstract class RoomActivity
    implements _is.SerializableModel, _is.ProtocolSerialization {
  RoomActivity._({
    required this.kind,
    required this.displayName,
    required this.content,
    required this.createdAt,
  });

  factory RoomActivity({
    required String kind,
    required String displayName,
    required String content,
    required DateTime createdAt,
  }) = _RoomActivityImpl;

  factory RoomActivity.fromJson(Map<String, dynamic> jsonSerialization) {
    return RoomActivity(
      kind: jsonSerialization['kind'] as String,
      displayName: jsonSerialization['displayName'] as String,
      content: jsonSerialization['content'] as String,
      createdAt: _is.DateTimeJsonExtension.fromJson(
        jsonSerialization['createdAt'],
      ),
    );
  }

  String kind;

  String displayName;

  String content;

  DateTime createdAt;

  /// Returns a shallow copy of this [RoomActivity]
  /// with some or all fields replaced by the given arguments.
  @_is.useResult
  RoomActivity copyWith({
    String? kind,
    String? displayName,
    String? content,
    DateTime? createdAt,
  });
  @override
  Map<String, dynamic> toJson() {
    return {
      '__className__': 'RoomActivity',
      'kind': kind,
      'displayName': displayName,
      'content': content,
      'createdAt': createdAt.toJson(),
    };
  }

  @override
  Map<String, dynamic> toJsonForProtocol() {
    return {
      '__className__': 'RoomActivity',
      'kind': kind,
      'displayName': displayName,
      'content': content,
      'createdAt': createdAt.toJson(),
    };
  }

  @override
  String toString() {
    return _is.SerializationManager.encode(this);
  }
}

class _RoomActivityImpl extends RoomActivity {
  _RoomActivityImpl({
    required String kind,
    required String displayName,
    required String content,
    required DateTime createdAt,
  }) : super._(
         kind: kind,
         displayName: displayName,
         content: content,
         createdAt: createdAt,
       );

  /// Returns a shallow copy of this [RoomActivity]
  /// with some or all fields replaced by the given arguments.
  @_is.useResult
  @override
  RoomActivity copyWith({
    String? kind,
    String? displayName,
    String? content,
    DateTime? createdAt,
  }) {
    return RoomActivity(
      kind: kind ?? this.kind,
      displayName: displayName ?? this.displayName,
      content: content ?? this.content,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
