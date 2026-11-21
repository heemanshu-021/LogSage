import 'package:material_ui/material_ui.dart';
import 'package:serverpod_auth_idp_flutter/serverpod_auth_idp_flutter.dart';

import '../client.dart';
import 'incident_room_screen.dart';

class IncidentRoomHomeScreen extends StatefulWidget {
  const IncidentRoomHomeScreen({super.key});

  @override
  State<IncidentRoomHomeScreen> createState() => _IncidentRoomHomeScreenState();
}

class _IncidentRoomHomeScreenState extends State<IncidentRoomHomeScreen> {
  final _displayName = TextEditingController();
  final _incidentId = TextEditingController();
  final _incidentTitle = TextEditingController();
  final _joinCode = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _displayName.dispose();
    _incidentId.dispose();
    _incidentTitle.dispose();
    _joinCode.dispose();
    super.dispose();
  }

  Future<void> _createRoom() async {
    await _run(() async {
      final room = await client.incidentRoom.createRoom(
        incidentId: _incidentId.text,
        incidentTitle: _incidentTitle.text,
        displayName: _displayName.text,
      );
      await _openRoom(room.joinCode);
    });
  }

  Future<void> _joinRoom() async {
    await _run(() async {
      final snapshot = await client.incidentRoom.joinRoom(
        joinCode: _joinCode.text,
        displayName: _displayName.text,
      );
      await _openRoom(snapshot.room.joinCode);
    });
  }

  Future<void> _run(Future<void> Function() operation) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await operation();
    } catch (error) {
      if (mounted) setState(() => _error = _readableError(error));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _openRoom(String code) async {
    if (!mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => IncidentRoomScreen(joinCode: code),
      ),
    );
  }

  String _readableError(Object error) {
    final text = error.toString();
    return text.startsWith('Exception: ')
        ? text.substring('Exception: '.length)
        : text;
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text('LogSage incident rooms'),
        actions: [
          IconButton(
            tooltip: 'Sign out',
            onPressed: () => client.auth.signOutDevice(),
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 980),
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Text(
                'Respond together',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 8),
              Text(
                'Create a shared room for an incident, or join your team with its room code. Notes and participants update live for everyone.',
                style: Theme.of(context).textTheme.bodyLarge,
              ),
              const SizedBox(height: 24),
              TextField(
                controller: _displayName,
                maxLength: 80,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(
                  labelText: 'Your name in the room',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              LayoutBuilder(
                builder: (context, constraints) {
                  final createCard = _createCard(context, colors);
                  final joinCard = _joinCard(context, colors);
                  if (constraints.maxWidth < 720) {
                    return Column(
                      children: [
                        createCard,
                        const SizedBox(height: 16),
                        joinCard,
                      ],
                    );
                  }
                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(child: createCard),
                      const SizedBox(width: 16),
                      Expanded(child: joinCard),
                    ],
                  );
                },
              ),
              if (_error != null) ...[
                const SizedBox(height: 16),
                Text(_error!, style: TextStyle(color: colors.error)),
              ],
              if (_busy) ...[
                const SizedBox(height: 16),
                const LinearProgressIndicator(),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _createCard(BuildContext context, ColorScheme colors) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Start an incident room',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _incidentId,
              decoration: const InputDecoration(
                labelText: 'Incident ID',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _incidentTitle,
              decoration: const InputDecoration(
                labelText: 'Incident title',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _busy ? null : _createRoom,
              icon: const Icon(Icons.add_link),
              label: const Text('Create room'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _joinCard(BuildContext context, ColorScheme colors) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Join your team',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _joinCode,
              textCapitalization: TextCapitalization.characters,
              maxLength: 10,
              decoration: const InputDecoration(
                labelText: 'Room code',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: _busy ? null : _joinRoom,
              icon: const Icon(Icons.groups_outlined),
              label: const Text('Join room'),
            ),
          ],
        ),
      ),
    );
  }
}
