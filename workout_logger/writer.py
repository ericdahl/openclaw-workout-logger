"""
JSONL writer with git integration.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False


def formatCommitMessage(record: Dict[str, Any]) -> str:
    """
    Format a git commit message for a workout record.

    Examples:
        - "workout: squat 315x5x3 rpe8"
        - "note: Felt tired today"
    """
    if record.get('type') == 'note':
        notes = record.get('notes', '').strip()
        # Truncate long notes to 72 chars
        if len(notes) > 65:
            notes = notes[:65] + '...'
        return f"note: {notes}"

    exercise = record.get('exercise') or record.get('modality', 'workout')

    # Build concise summary
    parts = [exercise]

    # For strength/bodyweight/machine: extract sets info
    if record.get('sets'):
        sets = record['sets']
        if len(sets) > 0:
            # Check if all sets are uniform
            first_set = sets[0]
            all_same = all(
                s.get('weight') == first_set.get('weight') and s.get('reps') == first_set.get('reps')
                for s in sets
            )

            if all_same and len(sets) > 1:
                # Format: "315x5x3" (weight x count x reps)
                if first_set.get('weight'):
                    parts.append(f"{int(first_set['weight'])}x{len(sets)}x{first_set['reps']}")
                else:
                    parts.append(f"{len(sets)}x{first_set['reps']}")
            elif len(sets) == 1:
                # Single set
                if first_set.get('weight'):
                    parts.append(f"{int(first_set['weight'])}x{first_set['reps']}")
                else:
                    parts.append(f"{first_set['reps']}")
            else:
                # Variable sets - just show count
                parts.append(f"{len(sets)} sets")

    # Add RPE if present
    if record.get('rpe'):
        parts.append(f"rpe{record['rpe']}")

    msg = ' '.join(parts)

    # Truncate to 72 chars
    if len(msg) > 65:
        msg = msg[:65] + '...'

    return f"workout: {msg}"


def commitWorkout(filepath: Path, record: Dict[str, Any], auto_push: bool = True) -> None:
    """
    Auto-commit workout entry to git and optionally push.

    Args:
        filepath: Path to the JSONL file
        record: The workout record dict
        auto_push: If True, push to remote after committing
    """
    if not GIT_AVAILABLE:
        raise RuntimeError("GitPython not installed. Install with: pip install gitpython")

    try:
        # Find the git repository root
        repo = git.Repo(filepath, search_parent_directories=True)

        # Add the file to the index
        repo.index.add([str(filepath)])

        # Create commit message
        commit_msg = formatCommitMessage(record)

        # Commit with co-author
        full_msg = f"{commit_msg}\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

        repo.index.commit(full_msg)

        # Push to remote if requested
        if auto_push:
            origin = repo.remote(name='origin')
            origin.push()

    except git.exc.InvalidGitRepositoryError:
        raise RuntimeError(f"Not a git repository: {filepath.parent}")
    except Exception as e:
        raise RuntimeError(f"Git commit failed: {e}")


def writeWorkoutLog(record: Dict[str, Any], date: str, db_dir: Optional[Path] = None,
                    dry_run: bool = False, auto_commit: bool = True, auto_push: bool = True) -> Path:
    """
    Write workout record to JSONL file and optionally commit/push to git.

    Args:
        record: The workout record dict
        date: Date string in format "YYYY-MM-DD"
        db_dir: Database directory (defaults to ~/repos/fitness/db)
        dry_run: If True, don't write file or commit
        auto_commit: If True and not dry_run, commit to git
        auto_push: If True and auto_commit, push to remote after committing

    Returns:
        Path to the JSONL file
    """
    # Default database directory
    if db_dir is None:
        db_dir = Path.home() / 'repos' / 'fitness' / 'db'
    else:
        db_dir = Path(db_dir)

    # Parse date
    year, month, day = date.split('-')

    # Build filepath: {db_dir}/YYYY/MM/DD.jsonl
    filepath = db_dir / year / month / f'{day}.jsonl'

    if dry_run:
        return filepath

    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Append to JSONL
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')

    # Auto-commit to git (and optionally push)
    if auto_commit and GIT_AVAILABLE:
        try:
            commitWorkout(filepath, record, auto_push=auto_push)
        except RuntimeError as e:
            # Don't fail the write operation if git commit/push fails
            # Just warn (the CLI will handle this)
            pass

    return filepath
