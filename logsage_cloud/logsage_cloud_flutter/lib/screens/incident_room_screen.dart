import 'dart:async';

import 'package:material_ui/material_ui.dart';
import 'package:flutter/services.dart';
import 'package:logsage_cloud_client/logsage_cloud_client.dart';

import '../client.dart';

class IncidentRoomScreen extends StatefulWidget {
  const IncidentRoomScreen({required this.joinCode, super.key});

  final String joinCode;

  @override
  State<IncidentRoomScreen> createState() => _IncidentRoomScreenState();
}

class _IncidentRoomScreenState extends State<IncidentRoomScreen> {
  final _message = TextEditingController();
  final _scrollController = ScrollController();
  RoomSnapshot? _snapshot;
  final List<RoomActivity> _activity = [];
  StreamSubscription<RoomActivity>? _subscription;
  String? _error;
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _loadRoom();
  }

  @override
  void dispose() {
    _subscription?.cancel();
    _message.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadRoom() async {
    try {
      final snapshot = await client.incidentRoom.loadRoom(widget.joinCode);
      if (!mounted) return;
      setState(() {
        _snapshot = snapshot;
        _activity
          ..clear()
          ..addAll(
            snapshot.messages.map(
              (message) => RoomActivity(
                kind: 'message',
                displayName: message.authorName,
                content: message.content,
                createdAt: message.createdAt,
              ),
            ),
          );
      });
      _subscription = client.incidentRoom
          .watchRoom(widget.joinCode)
          .listen(
            _onActivity,
            onError: (Object error) {
              if (mounted) {
                setState(() => _error = 'Live updates disconnected: $error');
              }
            },
            onDone: () {
              if (mounted) {
                setState(
                  () => _error =
                      'Live updates disconnected. Reopen the room to reconnect.',
                );
              }
            },
          );
    } catch (error) {
      if (mounted) {
        setState(() => _error = error.toString());
      }
    }
  }

  void _onActivity(RoomActivity activity) {
    if (!mounted) return;
    setState(() {
      _activity.add(activity);
      if (_activity.length > 200) {
        _activity.removeAt(0);
      }
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 180),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage() async {
    final text = _message.text.trim();
    if (text.isEmpty || _sending) {
      return;
    }
    setState(() => _sending = true);
    try {
      await client.incidentRoom.postMessage(
        joinCode: widget.joinCode,
        content: text,
      );
      _message.clear();
      if (mounted) setState(() => _error = null);
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _copyCode() async {
    await Clipboard.setData(ClipboardData(text: widget.joinCode));
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Room code copied')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final snapshot = _snapshot;
    return Scaffold(
      appBar: AppBar(
        title: Text(snapshot?.room.incidentTitle ?? 'Incident room'),
        actions: [
          IconButton(
            tooltip: 'Copy room code',
            onPressed: _copyCode,
            icon: const Icon(Icons.copy),
          ),
        ],
      ),
      body: snapshot == null
          ? Center(
              child: _error == null
                  ? const CircularProgressIndicator()
                  : Padding(
                      padding: const EdgeInsets.all(24),
                      child: Text(_error!, textAlign: TextAlign.center),
                    ),
            )
          : Column(
              children: [
                _roomBanner(context, snapshot),
                if (_error != null)
                  MaterialBanner(
                    content: Text(_error!),
                    actions: [
                      TextButton(
                        onPressed: _loadRoom,
                        child: const Text('Reconnect'),
                      ),
                    ],
                  ),
                Expanded(child: _activityList(context)),
                _composer(),
              ],
            ),
    );
  }

  Widget _roomBanner(BuildContext context, RoomSnapshot snapshot) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      width: double.infinity,
      color: colors.surfaceContainerHighest,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      child: Wrap(
        alignment: WrapAlignment.spaceBetween,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 12,
        runSpacing: 8,
        children: [
          Text(
            'Incident ${snapshot.room.incidentId} · ${snapshot.participants.length} responders',
          ),
          SelectableText('Room code: ${snapshot.room.joinCode}'),
        ],
      ),
    );
  }

  Widget _activityList(BuildContext context) {
    if (_activity.isEmpty) {
      return const Center(
        child: Text('The room is ready. Share the code and coordinate here.'),
      );
    }
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.all(20),
      itemCount: _activity.length,
      itemBuilder: (context, index) {
        final item = _activity[index];
        final isJoin = item.kind == 'participant_joined';
        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: isJoin
              ? Center(
                  child: Text(
                    '${item.displayName} ${item.content}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                )
              : Align(
                  alignment: Alignment.centerLeft,
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 720),
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              item.displayName,
                              style: Theme.of(context).textTheme.labelLarge,
                            ),
                            const SizedBox(height: 4),
                            SelectableText(item.content),
                            const SizedBox(height: 4),
                            Text(
                              TimeOfDay.fromDateTime(
                                item.createdAt.toLocal(),
                              ).format(context),
                              style: Theme.of(context).textTheme.labelSmall,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
        );
      },
    );
  }

  Widget _composer() {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _message,
                minLines: 1,
                maxLines: 5,
                maxLength: 2000,
                onSubmitted: (_) => _sendMessage(),
                decoration: const InputDecoration(
                  hintText: 'Share an update or handoff note',
                  border: OutlineInputBorder(),
                  counterText: '',
                ),
              ),
            ),
            const SizedBox(width: 10),
            IconButton.filled(
              tooltip: 'Send update',
              onPressed: _sending ? null : _sendMessage,
              icon: _sending
                  ? const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.send),
            ),
          ],
        ),
      ),
    );
  }
}
