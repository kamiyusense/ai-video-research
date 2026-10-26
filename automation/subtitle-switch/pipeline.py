"""Durable one-button orchestration; service implementations are injected.

An in-flight write surviving a crash is read back, never blindly repeated.
This module has no network, model, subprocess or service imports.
"""
from __future__ import annotations

import os
from pathlib import Path

STAGES = ('intake', 'captions', 'transcript', 'research', 'review', 'catalog', 'github', 'notebook')
WRITES = {'github', 'notebook'}
TERMINAL = {'complete', 'ALREADY_REGISTERED', 'TRANSCRIPT_UNAVAILABLE'}


class StageFailure(Exception):
    def __init__(self, reason, waiting=False, global_stage=False, no_write=False):
        super().__init__(reason)
        self.reason, self.waiting, self.global_stage = reason, waiting, global_stage
        self.no_write = no_write


class InstanceLock:
    """OS lock releases on crash; the lock file itself may safely remain."""
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open('a+b')
        try:
            if os.name == 'nt':
                import msvcrt
                self.stream.seek(0)
                if not self.stream.read(1):
                    self.stream.write(b'0')
                    self.stream.flush()
                self.stream.seek(0)
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.stream.close()
            raise RuntimeError('ALREADY_RUNNING') from None
        return self

    def __exit__(self, *exc):
        self.stream.close()


class Pipeline:
    def __init__(self, inventory, services, notify=lambda: None):
        self.inventory, self.services, self.notify = inventory, services, notify

    def record(self):
        self.inventory.save()
        self.notify()

    def run(self, correction=''):
        blocked = {}
        for row in self.inventory.data['videos'].values():
            if row['rejected'] or row['status'] in TERMINAL:
                continue
            if row.get('failed') and not row.get('inflight'):
                if not correction or correction == row.get('last_correction'):
                    continue
                if row.get('corrected_retries', 0) >= 2:
                    row.update(status='attention', status_reason='RETRY_LIMIT')
                    self.record()
                    continue
                row['corrected_retries'] = row.get('corrected_retries', 0) + 1
                row['last_correction'] = correction
                row['failed'] = False
            for stage in STAGES:
                if stage in row['completed_stages']:
                    continue
                row['stage'] = stage
                if stage in blocked:
                    row.update(status='waiting', status_reason=blocked[stage], failed=True)
                    self.record()
                    break
                row['status'] = 'running'
                self.record()
                reconciling = row.get('inflight') == stage
                try:
                    if reconciling:
                        # The process may have died after sending the request.
                        result = self.services.readback(stage, row)
                        if result is None:
                            raise StageFailure('WRITE_RESULT_UNKNOWN', waiting=True)
                    else:
                        if stage in WRITES:
                            row['inflight'] = stage
                            self.record()
                        result = self.services.execute(stage, row)
                    result = result or {}
                    result['is_mock'] = bool(getattr(self.services, 'is_mock', False))
                    if result.get('terminal'):
                        row.update(status=result['terminal'], status_reason=result['terminal'])
                        row.pop('inflight', None)
                        self.record()
                        break
                    # Service adapters return metadata only, never document bodies.
                    row.setdefault('receipts', {})[stage] = result
                    row['completed_stages'].append(stage)
                    row.pop('inflight', None)
                    row.update(status='pending', status_reason='', failed=False)
                    self.record()
                except StageFailure as exc:
                    if exc.no_write and not reconciling:
                        row.pop('inflight', None)
                    row.update(status='waiting' if exc.waiting else 'attention', status_reason=exc.reason, failed=True)
                    if exc.global_stage:
                        blocked[stage] = exc.reason
                    self.record()
                    break
                except Exception:
                    # Exception strings may contain subprocess output or secrets.
                    row.update(status='attention', status_reason='UNKNOWN_STAGE_FAILURE', failed=True)
                    self.record()
                    break
            else:
                row.update(status='complete', status_reason='', failed=False)
                self.record()
