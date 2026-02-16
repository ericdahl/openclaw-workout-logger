"""
Click-based CLI interface for workout logger.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import click
from zoneinfo import ZoneInfo

from workout_logger.parser import parseWorkoutLog
from workout_logger.writer import writeWorkoutLog


PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Workout logger CLI - Log workouts to JSONL with git integration."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.argument('message')
@click.option('--dry-run', is_flag=True, help='Parse without writing to database')
@click.option('--db-dir', type=click.Path(), envvar='WORKOUT_LOGGER_DB',
              help='Database directory (default: ~/repos/fitness/db)')
@click.option('--date', 'date_override', help='Override date (YYYY-MM-DD)')
@click.option('--source', default='cli', help='Source identifier (default: cli)')
@click.option('--no-commit', is_flag=True, help='Skip git commit')
def log(message: str, dry_run: bool, db_dir: Optional[str], date_override: Optional[str],
        source: str, no_commit: bool):
    """
    Log a workout entry.

    Examples:

        \b
        workout-logger log "deadlift 405 5x2"
        workout-logger log "squat 315x5x3 rpe8 felt strong"
        workout-logger log "pull-up 20,20,25"
        workout-logger log "treadmill 10min 3.2mph incline15"

    Date modifiers:

        \b
        workout-logger log "yesterday: squat 315x5x3"
        workout-logger log "2026-01-30: deadlift 405x1x5"

    Options:

        \b
        workout-logger log "bench 225x5x3" --dry-run
        workout-logger log "squat 315x5x3" --date 2026-02-01
        workout-logger log "bench 225x5x3" --no-commit
    """
    # Strip /log or /note prefix if user accidentally included it (show warning)
    original_message = message
    if message.startswith('/log '):
        message = '/log ' + message[5:].strip()
        click.echo("⚠️  Note: No need to include '/log' prefix when using CLI", err=True)
    elif message.startswith('/note '):
        message = '/note ' + message[6:].strip()
        click.echo("⚠️  Note: No need to include '/note' prefix when using CLI", err=True)
    else:
        # Add /log prefix for parser
        message = '/log ' + message

    try:
        # Parse timestamp
        timestamp = None
        if date_override:
            # Parse the date override
            try:
                year, month, day = date_override.split('-')
                now = datetime.now(PACIFIC_TZ)
                timestamp = datetime(int(year), int(month), int(day),
                                   now.hour, now.minute, now.second, tzinfo=PACIFIC_TZ)
            except ValueError:
                click.echo(f"❌ Invalid date format: {date_override}. Use YYYY-MM-DD", err=True)
                sys.exit(1)

        # Parse the workout message
        record, date_str = parseWorkoutLog(message, timestamp=timestamp, source=source)

        # Resolve db_dir
        db_path = Path(db_dir) if db_dir else None

        # Write to JSONL
        filepath = writeWorkoutLog(
            record,
            date_str,
            db_dir=db_path,
            dry_run=dry_run,
            auto_commit=not no_commit
        )

        # Show output
        if dry_run:
            click.echo(json.dumps(record, indent=2))
            click.echo(f"\n📝 Dry run: would save to {filepath}")
        else:
            click.echo(f"✓ Logged to {filepath}")
            if not no_commit:
                click.echo("✓ Committed to git")

    except ValueError as e:
        click.echo(f"❌ Parse error: {e}", err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('message')
@click.option('--dry-run', is_flag=True, help='Parse without writing to database')
@click.option('--db-dir', type=click.Path(), envvar='WORKOUT_LOGGER_DB',
              help='Database directory (default: ~/repos/fitness/db)')
@click.option('--date', 'date_override', help='Override date (YYYY-MM-DD)')
@click.option('--source', default='cli', help='Source identifier (default: cli)')
@click.option('--no-commit', is_flag=True, help='Skip git commit')
def note(message: str, dry_run: bool, db_dir: Optional[str], date_override: Optional[str],
         source: str, no_commit: bool):
    """
    Log a note entry.

    Examples:

        \b
        workout-logger note "Felt tired today"
        workout-logger note "Skipped workout due to illness"
    """
    # Strip /note prefix if user accidentally included it
    if message.startswith('/note '):
        message = '/note ' + message[6:].strip()
        click.echo("⚠️  Note: No need to include '/note' prefix when using CLI", err=True)
    else:
        # Add /note prefix for parser
        message = '/note ' + message

    try:
        # Parse timestamp
        timestamp = None
        if date_override:
            try:
                year, month, day = date_override.split('-')
                now = datetime.now(PACIFIC_TZ)
                timestamp = datetime(int(year), int(month), int(day),
                                   now.hour, now.minute, now.second, tzinfo=PACIFIC_TZ)
            except ValueError:
                click.echo(f"❌ Invalid date format: {date_override}. Use YYYY-MM-DD", err=True)
                sys.exit(1)

        # Parse the note message
        record, date_str = parseWorkoutLog(message, timestamp=timestamp, source=source)

        # Resolve db_dir
        db_path = Path(db_dir) if db_dir else None

        # Write to JSONL
        filepath = writeWorkoutLog(
            record,
            date_str,
            db_dir=db_path,
            dry_run=dry_run,
            auto_commit=not no_commit
        )

        # Show output
        if dry_run:
            click.echo(json.dumps(record, indent=2))
            click.echo(f"\n📝 Dry run: would save to {filepath}")
        else:
            click.echo(f"✓ Note logged to {filepath}")
            if not no_commit:
                click.echo("✓ Committed to git")

    except ValueError as e:
        click.echo(f"❌ Parse error: {e}", err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
