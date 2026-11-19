INSERT INTO EVACUATION_ZONE (zone_id, zone_name) VALUES
    (1, 'Zone A - Riverside'),
    (2, 'Zone B - Hillcrest'),
    (3, 'Zone C - Lakeview'),
    (4, 'Zone D - Pinewood'),
    (5, 'Zone E - Industrial Park');

INSERT INTO EMERGENCY_EVENT (event_id, name, event_type, start_date, end_date, status) VALUES
    (1, 'Foothills Wildfire 2026', 'Wildfire', '2026-08-02', NULL, 'Active'),
    (2, 'Spring River Flood 2026', 'Flood', '2026-04-18', '2026-05-10', 'Closed');

INSERT INTO STAFF (staff_id, name, login_email, password_hash) VALUES
    (1, 'Maria Chen',     'maria.chen@evacbridge.example',    'sample_hash_staff_1'),
    (2, 'Omar Haddad',    'omar.haddad@evacbridge.example',   'sample_hash_staff_2'),
    (3, 'Priya Singh',    'priya.singh@evacbridge.example',   'sample_hash_staff_3'),
    (4, 'Liam O''Connor', 'liam.oconnor@evacbridge.example',  'sample_hash_staff_4');

-- available_spaces starts equal to capacity, then Part 2b recalculates it
INSERT INTO SHELTER (shelter_id, name, address, capacity, operating_status, available_spaces) VALUES
    (1, 'Northside Recreation Centre', '4100 Centre Street',  120, 'Open',   120),
    (2, 'Hillcrest High School Gym',   '210 School Road',      80, 'Open',    80),
    (3, 'Lakeview Community Hall',     '55 Lakeview Drive',    60, 'Open',    60),
    (4, 'Old Arena',                   '9 Arena Road',        100, 'Closed', 100);

INSERT INTO MANAGES (staff_id, shelter_id) VALUES
    (1, 1), (1, 2), (2, 2), (3, 3);

INSERT INTO HOUSEHOLD (household_id, street, city, province, postal_code, zone_id) VALUES
    (1, '12 Maple Street',    'Fort McMurray', 'Alberta', 'T9H 1A1', 1),
    (2, '88 Birch Avenue',    'Fort McMurray', 'Alberta', 'T9H 2B2', 1),
    (3, '41 Hillcrest Road',  'Fort McMurray', 'Alberta', 'T9K 3C3', 2),
    (4, '7 Lakeview Drive',   'Fort McMurray', 'Alberta', 'T9J 4D4', 3),
    (5, '23 Pine Crescent',   'Fort McMurray', 'Alberta', 'T9K 5E5', 4),
    (6, '150 Industrial Way', 'Fort McMurray', 'Alberta', 'T9H 6F6', 5);

INSERT INTO HOUSEHOLD_MEMBER (member_id, first_name, last_name, date_of_birth, phone_number, household_id) VALUES
    (1,  'Anh',      'Nguyen',   '1980-03-14', '780-555-0101', 1),
    (2,  'Linh',     'Nguyen',   '1983-07-22', '780-555-0102', 1),
    (3,  'Minh',     'Nguyen',   '2012-05-09', NULL,           1),
    (4,  'Chidi',    'Okafor',   '1975-11-30', '780-555-0111', 2),
    (5,  'Ada',      'Okafor',   '1978-02-05', NULL,           2),
    (6,  'Emeka',    'Okafor',   '2008-09-17', NULL,           2),
    (7,  'Ngozi',    'Okafor',   '2015-01-28', NULL,           2),
    (8,  'Sophie',   'Tremblay', '1990-06-12', '780-555-0131', 3),
    (9,  'Lucas',    'Tremblay', '2019-10-03', NULL,           3),
    (10, 'Daniel',   'Bear',     '1968-04-25', '780-555-0141', 4),
    (11, 'Rosa',     'Bear',     '1970-12-08', NULL,           4),
    (12, 'Marek',    'Kowalski', '1985-08-19', '780-555-0151', 5),
    (13, 'Ewa',      'Kowalski', '1987-01-11', '780-555-0152', 5),
    (14, 'Harpreet', 'Singh',    '1992-09-02', '780-555-0161', 6);

INSERT INTO ACCOUNT_HOLDER (member_id, login_email, password_hash) VALUES
    (1,  'anh.nguyen@household.example',      'sample_hash_member_1'),
    (2,  'linh.nguyen@household.example',     'sample_hash_member_2'),
    (4,  'chidi.okafor@household.example',    'sample_hash_member_4'),
    (8,  'sophie.tremblay@household.example', 'sample_hash_member_8'),
    (10, 'daniel.bear@household.example',     'sample_hash_member_10'),
    (12, 'marek.kowalski@household.example',  'sample_hash_member_12'),
    (14, 'harpreet.singh@household.example',  'sample_hash_member_14');

INSERT INTO EVACUATION_NOTICE (notice_id, title, message, published_at, event_id, staff_id) VALUES
    (1, 'Evacuation Order: Riverside and Hillcrest',
        'Leave now. Zone A and Zone B must evacuate. Register for shelter in EvacBridge.',
        '2026-08-02 12:00:00', 1, 1),
    (2, 'Evacuation Alert: Lakeview and Pinewood',
        'Zone C and Zone D should be ready to leave on short notice.',
        '2026-08-02 20:30:00', 1, 2),
    (3, 'Shelter Update',
        'Shelters in Hillcrest and Lakeview are accepting arrivals. Check available spaces before you register.',
        '2026-08-03 08:00:00', 1, 3),
    (4, 'Flood Warning: Riverside',
        'River levels are rising in Zone A. Move to higher ground.',
        '2026-04-18 06:00:00', 2, 2);

INSERT INTO NOTICE_ZONE (notice_id, zone_id) VALUES
    (1, 1), (1, 2), (2, 3), (2, 4), (3, 1), (3, 2), (3, 3), (4, 1);

INSERT INTO REGISTRATION (registration_id, submitted_at, status, household_id, event_id, submitter_id) VALUES
    (1, '2026-08-02 14:10:00', 'Active', 1, 1, 1),
    (2, '2026-08-02 15:30:00', 'Active', 2, 1, 4),
    (3, '2026-08-03 09:05:00', 'Active', 3, 1, 8),
    (4, '2026-08-03 10:20:00', 'Active', 4, 1, 10),
    (5, '2026-08-03 16:45:00', 'Active', 5, 1, 12),
    (6, '2026-04-19 08:00:00', 'Active', 1, 2, 2);

-- Only participating members are listed (registration 5 and 6 do not include everyone)
INSERT INTO REGISTRATION_MEMBER (registration_id, member_id) VALUES
    (1, 1), (1, 2), (1, 3),
    (2, 4), (2, 5), (2, 6), (2, 7),
    (3, 8), (3, 9),
    (4, 10), (4, 11),
    (5, 12),
    (6, 1), (6, 3);

INSERT INTO PLACEMENT (registration_id, placement_no, created_at, arrival_time, departure_time, status, shelter_id) VALUES
    (1, 1, '2026-08-02 14:15:00', '2026-08-02 17:00:00', '2026-08-03 11:00:00', 'Transferred', 1),
    (1, 2, '2026-08-03 11:05:00', '2026-08-03 12:00:00', NULL,                  'Arrived',     2),
    (2, 1, '2026-08-02 15:35:00', '2026-08-02 18:20:00', NULL,                  'Arrived',     1),
    (3, 1, '2026-08-03 09:10:00', NULL,                  NULL,                  'Reserved',    3),
    (4, 1, '2026-08-03 10:25:00', NULL,                  NULL,                  'Reserved',    2),
    (5, 1, '2026-08-03 16:50:00', NULL,                  NULL,                  'Reserved',    2),
    (6, 1, '2026-04-19 08:05:00', '2026-04-19 10:00:00', '2026-05-02 12:00:00', 'Departed',    1);

INSERT INTO REUNIFICATION_REQUEST
    (request_id, sought_person_name, sought_person_dob, other_info, submitted_at, status, staff_response, reviewed_at, event_id, requester_id, reviewer_id) VALUES
    (1, 'Marek Kowalski', NULL, 'Neighbour from Pine Crescent',
        '2026-08-03 18:00:00', 'Pending', NULL, NULL, 1, 14, NULL),
    (2, 'Sophie Tremblay', NULL, 'Friend with a young child',
        '2026-08-03 19:10:00', 'Responded',
        'A matching household has been found. Staff will contact you to arrange a call.',
        '2026-08-04 09:15:00', 1, 12, 3),
    (3, 'Ewa Kowalska', '1987-01-11', 'Colleague, may be registered under a different spelling',
        '2026-08-04 07:40:00', 'Pending', NULL, NULL, 1, 4, NULL);

INSERT INTO POSSIBLE_MATCH (request_id, registration_id, placement_no) VALUES
    (2, 3, 1),
    (3, 2, 1),
    (3, 5, 1);

-- ---------------------------------------------------------------------
-- PART 2b: KEEP SHELTER.available_spaces CORRECT
-- available_spaces = capacity - participating members in active placements
-- (active = Reserved or Arrived). Run this after every placement,
-- registration-member or capacity change.
-- ---------------------------------------------------------------------
UPDATE SHELTER
SET available_spaces = capacity - (
    SELECT COUNT(*)
    FROM PLACEMENT p
    JOIN REGISTRATION_MEMBER rm ON rm.registration_id = p.registration_id
    WHERE p.shelter_id = SHELTER.shelter_id
      AND p.status IN ('Reserved', 'Arrived')
)
WHERE shelter_id > 0;   -- key column in WHERE, so MySQL safe update mode accepts it
