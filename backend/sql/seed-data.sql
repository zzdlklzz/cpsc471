-- EvacBridge: development and API test data.
--
-- Run this once after schema-v1.sql in a fresh development/test database.
-- The script uses fixed IDs so API requests and expected results are repeatable.
-- It is not intended for production or for a database containing real data.
--
-- Household test logins (Django PBKDF2 hashes are stored below):
--   primary@example.test  / PrimaryPass123!
--   second@example.test   / SecondPass123!
--   other@example.test    / OtherPass123!
--
-- Supporting publisher data is required by EVACUATION_NOTICE.staff_id.
--   publisher@example.test / StaffPass123!
--
-- Main API scenarios:
--   household 1001: zone 101; use with X-Dev-Household-ID during development
--   household 1002: zone 102; ownership and final-account-holder checks
--   member 1101: registration submitter; deletion must be rejected
--   member 1102: ordinary unreferenced member; may be edited/deleted
--   member 1103: ordinary member ready for account enabling
--   member 1104: registration participant; deletion must be rejected
--   member 1105: unreferenced second account holder; may be deleted safely
--   member 1201: household 1002's final account holder; deletion must be rejected
--   notice 3003: belongs to two zones; list queries must not duplicate it

-- Predefined zones for zone lookup, signup, household editing, and notice filters.
INSERT INTO EVACUATION_ZONE (zone_id, zone_name) VALUES
    (101, 'North Ridge'),
    (102, 'River District'),
    (103, 'South Foothills');

INSERT INTO HOUSEHOLD (
    household_id,
    street,
    city,
    province,
    postal_code,
    zone_id
) VALUES
    (1001, '10 Aspen Way', 'Calgary', 'Alberta', 'T2N 1N4', 101),
    (1002, '25 River Road', 'Calgary', 'Alberta', 'T2P 2M5', 102);

INSERT INTO HOUSEHOLD_MEMBER (
    member_id,
    first_name,
    last_name,
    date_of_birth,
    phone_number,
    household_id
) VALUES
    (1101, 'Alex', 'Morgan', '1988-02-14', '403-555-0101', 1001),
    (1102, 'Jordan', 'Morgan', '2010-07-09', NULL, 1001),
    (1103, 'Riley', 'Morgan', '2004-11-23', '403-555-0103', 1001),
    (1104, 'Taylor', 'Morgan', '2015-03-18', NULL, 1001),
    (1105, 'Casey', 'Morgan', '1990-08-30', '403-555-0105', 1001),
    (1201, 'Sam', 'Patel', '1985-05-12', '403-555-0201', 1002),
    (1202, 'Jamie', 'Patel', '2012-12-01', NULL, 1002);

INSERT INTO ACCOUNT_HOLDER (member_id, login_email, password_hash) VALUES
    (
        1101,
        'primary@example.test',
        CONCAT(
            'pbkdf2_sha256$1000000$evacbridgeprimary1000$',
            'jJZxvP3PXIpNsvymsOhlHFoD1OoW5/e4woNGGA7Zbbs='
        )
    ),
    (
        1105,
        'second@example.test',
        CONCAT(
            'pbkdf2_sha256$1000000$evacbridgesecond1002$',
            'Di0D+3w1fOAKl9oEDi3+JcA20bvYsZH8DYiHG5qs6Ho='
        )
    ),
    (
        1201,
        'other@example.test',
        CONCAT(
            'pbkdf2_sha256$1000000$evacbridgeother2000$',
            'T09p7rtsXtr3/+87p2ChrpWzFX1hHyfUaYGSVuy8wcY='
        )
    );

INSERT INTO STAFF (staff_id, name, login_email, password_hash) VALUES
    (
        9001,
        'Mock Notice Publisher',
        'publisher@example.test',
        CONCAT(
            'pbkdf2_sha256$1000000$evacbridgestaff9000$',
            'XqLFmrN7yysAmQc+9Ei8pEMf9Db0st9x6jfamqUGYwo='
        )
    );

INSERT INTO EMERGENCY_EVENT (
    event_id,
    name,
    event_type,
    start_date,
    end_date,
    status
) VALUES
    (2001, 'North Ridge Wildfire', 'Wildfire', '2026-05-01', NULL, 'active'),
    (2002, 'Spring River Flood', 'Flood', '2026-04-10', '2026-04-18', 'resolved');

-- Publication times are deliberately different to verify newest-first ordering.
INSERT INTO EVACUATION_NOTICE (
    notice_id,
    title,
    message,
    published_at,
    event_id,
    staff_id
) VALUES
    (
        3001,
        'North Ridge evacuation alert',
        'Residents in North Ridge should prepare to leave immediately.',
        '2026-05-01 08:00:00',
        2001,
        9001
    ),
    (
        3002,
        'River District monitoring notice',
        'Residents near the river should monitor official updates.',
        '2026-05-01 09:00:00',
        2001,
        9001
    ),
    (
        3003,
        'Wildfire evacuation order expanded',
        'The evacuation order now includes North Ridge and River District.',
        '2026-05-01 10:30:00',
        2001,
        9001
    ),
    (
        3004,
        'South Foothills advisory',
        'Smoke may reduce visibility in South Foothills.',
        '2026-05-01 11:15:00',
        2001,
        9001
    ),
    (
        3005,
        'River levels returned to normal',
        'The Spring River Flood event is resolved.',
        '2026-04-18 16:00:00',
        2002,
        9001
    );

INSERT INTO NOTICE_ZONE (notice_id, zone_id) VALUES
    (3001, 101),
    (3002, 102),
    (3003, 101),
    (3003, 102),
    (3004, 103),
    (3005, 102);

-- These records exist specifically to exercise safe member-removal rules.
-- Member 1101 is the submitter while member 1104 is a participant.
INSERT INTO REGISTRATION (
    registration_id,
    submitted_at,
    status,
    household_id,
    event_id,
    submitter_id
) VALUES
    (4001, '2026-05-01 10:45:00', 'registered', 1001, 2001, 1101);

INSERT INTO REGISTRATION_MEMBER (registration_id, member_id) VALUES
    (4001, 1104);
