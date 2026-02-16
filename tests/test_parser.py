"""
Test cases for the workout log parser.
"""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from workout_logger.parser import (
    parseWorkoutLog,
    parseDate,
    normalizeExercise,
    parseRepList,
)

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


class TestExerciseNormalization:
    """Test exercise alias normalization."""

    def test_squat_aliases(self):
        assert normalizeExercise('squat') == 'squat'
        assert normalizeExercise('sq') == 'squat'
        assert normalizeExercise('Squat') == 'squat'
        assert normalizeExercise('SQ') == 'squat'

    def test_bench_aliases(self):
        assert normalizeExercise('bench') == 'bench_press'
        assert normalizeExercise('bp') == 'bench_press'
        assert normalizeExercise('bench press') == 'bench_press'

    def test_deadlift_aliases(self):
        assert normalizeExercise('deadlift') == 'deadlift'
        assert normalizeExercise('dl') == 'deadlift'

    def test_ohp_aliases(self):
        assert normalizeExercise('ohp') == 'ohp'
        assert normalizeExercise('op') == 'ohp'
        assert normalizeExercise('press') == 'ohp'
        assert normalizeExercise('overhead press') == 'ohp'

    def test_pullup_aliases(self):
        assert normalizeExercise('pull up') == 'pull_up'
        assert normalizeExercise('pull-up') == 'pull_up'
        assert normalizeExercise('pullup') == 'pull_up'

    def test_weighted_pullup_aliases(self):
        assert normalizeExercise('weighted pull up') == 'weighted_pull_up'
        assert normalizeExercise('weighted pull-up') == 'weighted_pull_up'
        assert normalizeExercise('weighted pullup') == 'weighted_pull_up'

    def test_treadmill_aliases(self):
        assert normalizeExercise('treadmill') == 'treadmill'
        assert normalizeExercise('tm') == 'treadmill'

    def test_unknown_exercise(self):
        assert normalizeExercise('foobar') is None


class TestDateParsing:
    """Test date parsing logic."""

    def test_no_date_returns_today(self):
        base = datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ)
        date_obj, year, month, day = parseDate(None, base)
        assert year == '2026'
        assert month == '02'
        assert day == '16'

    def test_yesterday(self):
        base = datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ)
        date_obj, year, month, day = parseDate('yesterday', base)
        assert year == '2026'
        assert month == '02'
        assert day == '15'

    def test_today(self):
        base = datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ)
        date_obj, year, month, day = parseDate('today', base)
        assert year == '2026'
        assert month == '02'
        assert day == '16'

    def test_iso_date(self):
        base = datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ)
        date_obj, year, month, day = parseDate('2026-01-30', base)
        assert year == '2026'
        assert month == '01'
        assert day == '30'

    def test_invalid_date(self):
        with pytest.raises(ValueError, match='Could not parse date'):
            parseDate('invalid', datetime.now(PACIFIC_TZ))


class TestRepListParsing:
    """Test comma-separated rep list parsing."""

    def test_simple_reps(self):
        result = parseRepList('20,20,25')
        assert result == [
            {'reps': 20},
            {'reps': 20},
            {'reps': 25},
        ]

    def test_failed_sets(self):
        result = parseRepList('2,1,x')
        assert result == [
            {'reps': 2},
            {'reps': 1},
            {'reps': 0, 'failed': True},
        ]

    def test_failed_with_f(self):
        result = parseRepList('5,4,f')
        assert result == [
            {'reps': 5},
            {'reps': 4},
            {'reps': 0, 'failed': True},
        ]


class TestStrengthWorkouts:
    """Test strength workout parsing."""

    def test_squat_315x5x3_with_rpe(self):
        record, date = parseWorkoutLog('/log squat 315x5x3 rpe8 felt strong',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['type'] == 'strength'
        assert record['exercise'] == 'squat'
        assert record['unit'] == 'lb'
        assert len(record['sets']) == 5
        assert all(s['weight'] == 315 and s['reps'] == 3 for s in record['sets'])
        assert record['rpe'] == 8
        assert 'felt strong' in record['notes']

    def test_bench_225x3x5(self):
        record, date = parseWorkoutLog('/log bench 225x3x5',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['type'] == 'strength'
        assert record['exercise'] == 'bench_press'
        assert record['unit'] == 'lb'
        assert len(record['sets']) == 3
        assert all(s['weight'] == 225 and s['reps'] == 5 for s in record['sets'])

    def test_deadlift_405_1x3(self):
        record, date = parseWorkoutLog('/log dl 405 1x3 rpe9',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['type'] == 'strength'
        assert record['exercise'] == 'deadlift'
        assert record['unit'] == 'lb'
        assert len(record['sets']) == 1
        assert record['sets'][0]['weight'] == 405
        assert record['sets'][0]['reps'] == 3
        assert record['rpe'] == 9

    def test_failed_sets(self):
        record, date = parseWorkoutLog('/log squat 405 2,1,x',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['type'] == 'strength'
        assert len(record['sets']) == 3
        assert record['sets'][0]['reps'] == 2
        assert record['sets'][1]['reps'] == 1
        assert record['sets'][2]['reps'] == 0
        assert record['sets'][2]['failed'] is True


class TestBodyweightWorkouts:
    """Test bodyweight workout parsing."""

    def test_pullup_comma_separated(self):
        record, date = parseWorkoutLog('/log pull-up 20,20,25',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['type'] == 'bodyweight'
        assert record['exercise'] == 'pull_up'
        assert len(record['sets']) == 3
        assert record['sets'][0]['reps'] == 20
        assert record['sets'][1]['reps'] == 20
        assert record['sets'][2]['reps'] == 25
        assert 'weight' not in record['sets'][0]

    def test_pullup_uniform_sets(self):
        record, date = parseWorkoutLog('/log pull-up 7x10',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['type'] == 'bodyweight'
        assert len(record['sets']) == 7
        assert all(s['reps'] == 10 for s in record['sets'])

    def test_weighted_pullup(self):
        record, date = parseWorkoutLog('/log weighted pull-up 25x5x10',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['type'] == 'bodyweight'
        assert record['exercise'] == 'weighted_pull_up'
        assert len(record['sets']) == 5
        assert all(s['weight'] == 25 and s['reps'] == 10 for s in record['sets'])


class TestMachineWorkouts:
    """Test machine workout parsing."""

    def test_leg_press(self):
        record, date = parseWorkoutLog('/log leg press 405x3x10',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['type'] == 'machine'
        assert record['exercise'] == 'leg_press'
        assert len(record['sets']) == 3
        assert all(s['weight'] == 405 and s['reps'] == 10 for s in record['sets'])

    def test_face_pulls(self):
        record, date = parseWorkoutLog('/log face pulls 60x3x15',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['type'] == 'machine'
        assert record['exercise'] == 'face_pulls'


class TestCardioWorkouts:
    """Test cardio workout parsing."""

    def test_treadmill_full(self):
        record, date = parseWorkoutLog('/log treadmill 10min 3.2mph incline15 steady pace',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['type'] == 'cardio'
        assert record['modality'] == 'treadmill'
        assert record['duration_min'] == 10
        assert record['speed_mph'] == 3.2
        assert record['incline_percent'] == 15
        assert 'steady pace' in record['notes']

    def test_treadmill_with_distance(self):
        record, date = parseWorkoutLog('/log treadmill 1 degree incline, 7.2 mph, 3.0 miles',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['type'] == 'cardio'
        assert record['modality'] == 'treadmill'
        assert record['incline_percent'] == 1
        assert record['speed_mph'] == 7.2
        assert record['distance_miles'] == 3.0

    def test_rowing(self):
        record, date = parseWorkoutLog('/log rowing 30min',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['type'] == 'cardio'
        assert record['modality'] == 'rowing'
        assert record['duration_min'] == 30


class TestNotes:
    """Test note entries."""

    def test_simple_note(self):
        record, date = parseWorkoutLog('/note Felt tired today',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['type'] == 'note'
        assert record['notes'] == 'Felt tired today'

    def test_note_with_date(self):
        record, date = parseWorkoutLog('/note yesterday: Skipped workout',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['type'] == 'note'
        assert date == '2026-02-15'


class TestDateModifiers:
    """Test date modifiers in workout logs."""

    def test_yesterday_at_start(self):
        record, date = parseWorkoutLog('/log yesterday: squat 315x5x3',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert date == '2026-02-15'
        assert record['exercise'] == 'squat'

    def test_specific_date_at_start(self):
        record, date = parseWorkoutLog('/log 2026-01-30: deadlift 405x1x5',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert date == '2026-01-30'
        assert record['exercise'] == 'deadlift'

    def test_specific_date_at_end(self):
        record, date = parseWorkoutLog('/log pull-up 20,27 2026-01-29',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert date == '2026-01-29'
        assert record['exercise'] == 'pull_up'


class TestErrorCases:
    """Test error handling."""

    def test_missing_log_prefix(self):
        with pytest.raises(ValueError, match='must start with /log or /note'):
            parseWorkoutLog('squat 315x5x3')

    def test_unknown_exercise(self):
        with pytest.raises(ValueError, match='Unknown exercise'):
            parseWorkoutLog('/log foobar 225x5x3')

    def test_no_exercise(self):
        with pytest.raises(ValueError, match='No exercise specified'):
            parseWorkoutLog('/log ')

    def test_invalid_format(self):
        with pytest.raises(ValueError, match='Could not parse format'):
            parseWorkoutLog('/log squat invalidformat')


class TestTimestampFormatting:
    """Test that timestamps are correctly formatted."""

    def test_timestamp_format(self):
        record, date = parseWorkoutLog('/log squat 315x5x3',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 45, tzinfo=PACIFIC_TZ))

        assert record['ts'].startswith('2026-02-16T10:30:45')
        assert '-08:00' in record['ts'] or '-07:00' in record['ts']  # PST or PDT

    def test_source_field(self):
        record, date = parseWorkoutLog('/log squat 315x5x3',
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ),
                                       source='test')

        assert record['source'] == 'test'

    def test_raw_field(self):
        msg = '/log squat 315x5x3 rpe8'
        record, date = parseWorkoutLog(msg,
                                       timestamp=datetime(2026, 2, 16, 10, 30, 0, tzinfo=PACIFIC_TZ))

        assert record['raw'] == msg
