-- =====================================================================
-- EvacBridge - CPSC 471 Group 29 - Progress Report #3 (Part c)
-- SQL DDL, sample data, update/delete statements and queries
-- Target DBMS: MySQL 8.0
-- The script can be run again and again because it drops the database first.
-- All sample data is made up for demonstration only.
-- =====================================================================

-- ---------------------------------------------------------------------
-- PART 1: CREATE DATABASE AND TABLES (15 tables, same as the final RM)
-- ---------------------------------------------------------------------
DROP DATABASE IF EXISTS evacbridge;
CREATE DATABASE evacbridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE evacbridge;

CREATE TABLE EVACUATION_ZONE (
    zone_id            INT NOT NULL AUTO_INCREMENT,
    zone_name          VARCHAR(100) NOT NULL,
    CONSTRAINT pk_evacuation_zone PRIMARY KEY (zone_id)
);

CREATE TABLE EMERGENCY_EVENT (
    event_id           INT NOT NULL AUTO_INCREMENT,
    name               VARCHAR(100) NOT NULL,
    event_type         VARCHAR(20)  NOT NULL,
    start_date         DATE         NOT NULL,
    end_date           DATE         NULL,
    status             VARCHAR(20)  NOT NULL DEFAULT 'Active',
    CONSTRAINT pk_emergency_event PRIMARY KEY (event_id),
    CONSTRAINT chk_event_type   CHECK (event_type IN ('Wildfire', 'Flood')),
    CONSTRAINT chk_event_status CHECK (status IN ('Active', 'Closed')),
    CONSTRAINT chk_event_dates  CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE STAFF (
    staff_id           INT NOT NULL AUTO_INCREMENT,
    name               VARCHAR(100) NOT NULL,
    login_email        VARCHAR(100) NOT NULL,
    password_hash      VARCHAR(255) NOT NULL,
    CONSTRAINT pk_staff PRIMARY KEY (staff_id),
    CONSTRAINT uq_staff_email UNIQUE (login_email)
);

CREATE TABLE HOUSEHOLD (
    household_id       INT NOT NULL AUTO_INCREMENT,
    street             VARCHAR(100) NOT NULL,
    city               VARCHAR(60)  NOT NULL,
    province           VARCHAR(30)  NOT NULL,
    postal_code        VARCHAR(10)  NOT NULL,
    zone_id            INT NOT NULL,
    CONSTRAINT pk_household PRIMARY KEY (household_id),
    CONSTRAINT fk_household_zone FOREIGN KEY (zone_id)
        REFERENCES EVACUATION_ZONE (zone_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE HOUSEHOLD_MEMBER (
    member_id          INT NOT NULL AUTO_INCREMENT,
    first_name         VARCHAR(50) NOT NULL,
    last_name          VARCHAR(50) NOT NULL,
    date_of_birth      DATE        NOT NULL,
    phone_number       VARCHAR(20) NULL,
    household_id       INT NOT NULL,
    CONSTRAINT pk_household_member PRIMARY KEY (member_id),
    CONSTRAINT fk_member_household FOREIGN KEY (household_id)
        REFERENCES HOUSEHOLD (household_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Partial specialization of HOUSEHOLD_MEMBER (members who have a login)
CREATE TABLE ACCOUNT_HOLDER (
    member_id          INT NOT NULL,
    login_email        VARCHAR(100) NOT NULL,
    password_hash      VARCHAR(255) NOT NULL,
    CONSTRAINT pk_account_holder PRIMARY KEY (member_id),
    CONSTRAINT uq_account_email UNIQUE (login_email),
    CONSTRAINT fk_account_member FOREIGN KEY (member_id)
        REFERENCES HOUSEHOLD_MEMBER (member_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE EVACUATION_NOTICE (
    notice_id          INT NOT NULL AUTO_INCREMENT,
    title              VARCHAR(150) NOT NULL,
    message            TEXT         NOT NULL,
    published_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_id           INT NOT NULL,
    staff_id           INT NOT NULL,
    CONSTRAINT pk_evacuation_notice PRIMARY KEY (notice_id),
    CONSTRAINT fk_notice_event FOREIGN KEY (event_id)
        REFERENCES EMERGENCY_EVENT (event_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_notice_staff FOREIGN KEY (staff_id)
        REFERENCES STAFF (staff_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- M:N "targeted at" between EVACUATION_NOTICE and EVACUATION_ZONE
CREATE TABLE NOTICE_ZONE (
    notice_id          INT NOT NULL,
    zone_id            INT NOT NULL,
    CONSTRAINT pk_notice_zone PRIMARY KEY (notice_id, zone_id),
    CONSTRAINT fk_nz_notice FOREIGN KEY (notice_id)
        REFERENCES EVACUATION_NOTICE (notice_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_nz_zone FOREIGN KEY (zone_id)
        REFERENCES EVACUATION_ZONE (zone_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE REGISTRATION (
    registration_id    INT NOT NULL AUTO_INCREMENT,
    submitted_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status             VARCHAR(20) NOT NULL DEFAULT 'Active',
    household_id       INT NOT NULL,
    event_id           INT NOT NULL,
    submitter_id       INT NULL,
    CONSTRAINT pk_registration PRIMARY KEY (registration_id),
    -- one registration per household for each emergency event
    CONSTRAINT uq_registration_household_event UNIQUE (household_id, event_id),
    CONSTRAINT chk_registration_status CHECK (status IN ('Active', 'Cancelled')),
    CONSTRAINT fk_registration_household FOREIGN KEY (household_id)
        REFERENCES HOUSEHOLD (household_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_registration_event FOREIGN KEY (event_id)
        REFERENCES EMERGENCY_EVENT (event_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_registration_submitter FOREIGN KEY (submitter_id)
        REFERENCES ACCOUNT_HOLDER (member_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- M:N "included in" between REGISTRATION and HOUSEHOLD_MEMBER
CREATE TABLE REGISTRATION_MEMBER (
    registration_id    INT NOT NULL,
    member_id          INT NOT NULL,
    CONSTRAINT pk_registration_member PRIMARY KEY (registration_id, member_id),
    CONSTRAINT fk_rm_registration FOREIGN KEY (registration_id)
        REFERENCES REGISTRATION (registration_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_rm_member FOREIGN KEY (member_id)
        REFERENCES HOUSEHOLD_MEMBER (member_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE SHELTER (
    shelter_id         INT NOT NULL AUTO_INCREMENT,
    name               VARCHAR(100) NOT NULL,
    address            VARCHAR(150) NOT NULL,
    capacity           INT          NOT NULL,
    operating_status   VARCHAR(20)  NOT NULL DEFAULT 'Open',
    available_spaces   INT          NOT NULL,
    CONSTRAINT pk_shelter PRIMARY KEY (shelter_id),
    CONSTRAINT chk_shelter_capacity CHECK (capacity > 0),
    CONSTRAINT chk_shelter_status   CHECK (operating_status IN ('Open', 'Closed')),
    CONSTRAINT chk_shelter_spaces   CHECK (available_spaces >= 0 AND available_spaces <= capacity)
);

-- M:N "manages" between STAFF and SHELTER
CREATE TABLE MANAGES (
    staff_id           INT NOT NULL,
    shelter_id         INT NOT NULL,
    CONSTRAINT pk_manages PRIMARY KEY (staff_id, shelter_id),
    CONSTRAINT fk_manages_staff FOREIGN KEY (staff_id)
        REFERENCES STAFF (staff_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_manages_shelter FOREIGN KEY (shelter_id)
        REFERENCES SHELTER (shelter_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Weak entity: owned by REGISTRATION, identified by (registration_id, placement_no)
CREATE TABLE PLACEMENT (
    registration_id    INT NOT NULL,
    placement_no       INT NOT NULL,
    created_at         DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    arrival_time       DATETIME    NULL,
    departure_time     DATETIME    NULL,
    status             VARCHAR(20) NOT NULL DEFAULT 'Reserved',
    shelter_id         INT NOT NULL,
    CONSTRAINT pk_placement PRIMARY KEY (registration_id, placement_no),
    CONSTRAINT chk_placement_no     CHECK (placement_no >= 1),
    CONSTRAINT chk_placement_status CHECK (status IN ('Reserved', 'Arrived', 'Departed', 'Transferred', 'Cancelled')),
    CONSTRAINT chk_placement_times  CHECK (arrival_time IS NULL OR departure_time IS NULL OR departure_time >= arrival_time),
    CONSTRAINT fk_placement_registration FOREIGN KEY (registration_id)
        REFERENCES REGISTRATION (registration_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_placement_shelter FOREIGN KEY (shelter_id)
        REFERENCES SHELTER (shelter_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE REUNIFICATION_REQUEST (
    request_id         INT NOT NULL AUTO_INCREMENT,
    sought_person_name VARCHAR(100) NOT NULL,
    sought_person_dob  DATE         NULL,
    other_info         VARCHAR(255) NULL,
    submitted_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status             VARCHAR(20)  NOT NULL DEFAULT 'Pending',
    staff_response     TEXT         NULL,
    reviewed_at        DATETIME     NULL,
    event_id           INT NOT NULL,
    requester_id       INT NOT NULL,
    reviewer_id        INT NULL,
    CONSTRAINT pk_reunification_request PRIMARY KEY (request_id),
    CONSTRAINT chk_request_status CHECK (status IN ('Pending', 'Responded')),
    CONSTRAINT chk_request_review CHECK (reviewed_at IS NULL OR reviewed_at >= submitted_at),
    CONSTRAINT chk_request_responded CHECK (status = 'Pending' OR (staff_response IS NOT NULL AND reviewed_at IS NOT NULL)),
    CONSTRAINT fk_request_event FOREIGN KEY (event_id)
        REFERENCES EMERGENCY_EVENT (event_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_request_requester FOREIGN KEY (requester_id)
        REFERENCES ACCOUNT_HOLDER (member_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_request_reviewer FOREIGN KEY (reviewer_id)
        REFERENCES STAFF (staff_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- M:N "possibly matches" between REUNIFICATION_REQUEST and PLACEMENT
CREATE TABLE POSSIBLE_MATCH (
    request_id         INT NOT NULL,
    registration_id    INT NOT NULL,
    placement_no       INT NOT NULL,
    CONSTRAINT pk_possible_match PRIMARY KEY (request_id, registration_id, placement_no),
    CONSTRAINT fk_pm_request FOREIGN KEY (request_id)
        REFERENCES REUNIFICATION_REQUEST (request_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_pm_placement FOREIGN KEY (registration_id, placement_no)
        REFERENCES PLACEMENT (registration_id, placement_no)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ---------------------------------------------------------------------
-- PART 2: SAMPLE DATA (inserted in an order that keeps referential integrity)
-- ---------------------------------------------------------------------
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

-- ---------------------------------------------------------------------
-- PART 3: UPDATE, INSERT AND DELETE STATEMENTS FOR EACH FUNCTION
-- (module numbers refer to the HIPO diagram)
-- ---------------------------------------------------------------------

-- 1.1 A new household creates its account (household, first member, login)
INSERT INTO HOUSEHOLD (household_id, street, city, province, postal_code, zone_id)
VALUES (7, '88 Maple Court', 'Fort McMurray', 'AB', 'T9H 2K4', 3);
INSERT INTO HOUSEHOLD_MEMBER (member_id, first_name, last_name, date_of_birth, phone_number, household_id)
VALUES (16, 'Leila', 'Haddad', '1990-06-02', '780-555-0166', 7);
INSERT INTO ACCOUNT_HOLDER (member_id, login_email, password_hash)
VALUES (16, 'leila.haddad@household.example', 'sample_hash_member_16');

-- 2.1.1 Household updates its details (household 6 moves to Zone B)
UPDATE HOUSEHOLD
SET street = '14 Hillcrest Road', zone_id = 2
WHERE household_id = 6;

-- 2.1.2 Household adds a member and updates a phone number
INSERT INTO HOUSEHOLD_MEMBER (member_id, first_name, last_name, date_of_birth, phone_number, household_id)
VALUES (15, 'Jaspreet', 'Singh', '2014-03-21', NULL, 6);

UPDATE HOUSEHOLD_MEMBER
SET phone_number = '780-555-0199'
WHERE member_id = 2;

-- 2.1.2 Household removes a member (Rosa leaves household 4).
-- ON DELETE CASCADE also removes her row in REGISTRATION_MEMBER.
DELETE FROM HOUSEHOLD_MEMBER
WHERE member_id = 11;

-- 1.1 / 2.1.2 A member is given a login (becomes an account holder)
INSERT INTO ACCOUNT_HOLDER (member_id, login_email, password_hash)
VALUES (13, 'ewa.kowalski@household.example', 'sample_hash_member_13');

-- 2.3.3 Household 6 registers for event 1 (space check first, then insert)
SELECT shelter_id, name, available_spaces
FROM SHELTER
WHERE shelter_id = 3 AND operating_status = 'Open' AND available_spaces >= 2;

INSERT INTO REGISTRATION (registration_id, submitted_at, status, household_id, event_id, submitter_id)
VALUES (7, '2026-08-04 10:05:00', 'Active', 6, 1, 14);

INSERT INTO REGISTRATION_MEMBER (registration_id, member_id) VALUES (7, 14), (7, 15);

INSERT INTO PLACEMENT (registration_id, placement_no, created_at, arrival_time, departure_time, status, shelter_id)
VALUES (7, 1, '2026-08-04 10:06:00', NULL, NULL, 'Reserved', 3);

-- 2.3.4 Household 5 replaces its participating members (Ewa now joins Marek)
DELETE FROM REGISTRATION_MEMBER WHERE registration_id = 5;
INSERT INTO REGISTRATION_MEMBER (registration_id, member_id) VALUES (5, 12), (5, 13);

-- 2.3.4 Household 4 cancels its registration and reservation
UPDATE REGISTRATION r
JOIN PLACEMENT p ON p.registration_id = r.registration_id
SET r.status = 'Cancelled', r.submitter_id = 10,
    p.status = 'Cancelled'
WHERE r.registration_id = 4 AND r.household_id = 4
  AND r.status = 'Active'
  AND p.status = 'Reserved' AND p.arrival_time IS NULL;

-- 2.4.1 Household submits a reunification request (starts as Pending)
INSERT INTO REUNIFICATION_REQUEST
    (request_id, sought_person_name, sought_person_dob, other_info, submitted_at, status, staff_response, reviewed_at, event_id, requester_id, reviewer_id)
VALUES (4, 'Tom Brandt', NULL, 'Coworker from the Hillcrest office', '2026-08-04 20:00:00', 'Pending', NULL, NULL, 1, 4, NULL);

-- 3.1.1 Staff create a new emergency event
INSERT INTO EMERGENCY_EVENT (event_id, name, event_type, start_date, end_date, status)
VALUES (3, 'Prairie Grass Fire 2026', 'Wildfire', '2026-09-12', NULL, 'Active');

-- 3.2.1 Staff publish a notice for two zones of the new event
INSERT INTO EVACUATION_NOTICE (notice_id, title, message, published_at, event_id, staff_id)
VALUES (5, 'Evacuation Alert: Pinewood and Industrial Park',
        'Zone D and Zone E should prepare to leave.', '2026-09-12 07:30:00', 3, 4);
INSERT INTO NOTICE_ZONE (notice_id, zone_id) VALUES (5, 4), (5, 5);

-- 3.1.2 Staff close the new event
UPDATE EMERGENCY_EVENT SET status = 'Closed', end_date = '2026-09-14' WHERE event_id = 3;

-- 3.3.2 and 3.3.1 Staff assign a staff member to the closed shelter, then open it
INSERT INTO MANAGES (staff_id, shelter_id) VALUES (4, 4);
UPDATE SHELTER SET operating_status = 'Open' WHERE shelter_id = 4;

-- 3.3.1 Staff increase the capacity of shelter 1
UPDATE SHELTER SET capacity = 140 WHERE shelter_id = 1;

-- 3.4.2 Staff record an arrival (registration 3 at shelter 3)
UPDATE PLACEMENT
SET status = 'Arrived', arrival_time = '2026-08-04 11:30:00'
WHERE registration_id = 3 AND placement_no = 1 AND status = 'Reserved';

-- 3.4.3 Staff record a departure (registration 2 leaves shelter 1)
UPDATE PLACEMENT
SET status = 'Departed', departure_time = '2026-08-05 09:00:00'
WHERE registration_id = 2 AND placement_no = 1 AND status = 'Arrived';

-- 3.4.4 Staff transfer registration 1 from shelter 2 to shelter 3.
-- The old placement is kept as history and a new one is created.
START TRANSACTION;

UPDATE PLACEMENT
SET status = 'Transferred', departure_time = '2026-08-05 12:00:00'
WHERE registration_id = 1 AND placement_no = 2 AND status = 'Arrived';

INSERT INTO PLACEMENT (registration_id, placement_no, created_at, status, shelter_id)
VALUES (1, 3, '2026-08-05 12:00:00', 'Reserved', 3);

UPDATE SHELTER
SET available_spaces = capacity - (
    SELECT COUNT(*)
    FROM PLACEMENT p
    JOIN REGISTRATION_MEMBER rm ON rm.registration_id = p.registration_id
    WHERE p.shelter_id = SHELTER.shelter_id
      AND p.status IN ('Reserved', 'Arrived')
)
WHERE shelter_id IN (2, 3);

COMMIT;

-- 3.5.2 Staff add a possible match for request 1 and rule out a wrong one for request 3
INSERT INTO POSSIBLE_MATCH (request_id, registration_id, placement_no) VALUES (1, 5, 1);
DELETE FROM POSSIBLE_MATCH
WHERE request_id = 3 AND registration_id = 2 AND placement_no = 1;

-- 3.5.3 Staff respond to request 3
UPDATE REUNIFICATION_REQUEST
SET status = 'Responded',
    staff_response = 'A possible match was found. Staff will contact you to confirm before sharing details.',
    reviewer_id = 3,
    reviewed_at = '2026-08-05 10:00:00'
WHERE request_id = 3 AND status = 'Pending';

-- Recalculate available_spaces after all changes above
UPDATE SHELTER
SET available_spaces = capacity - (
    SELECT COUNT(*)
    FROM PLACEMENT p
    JOIN REGISTRATION_MEMBER rm ON rm.registration_id = p.registration_id
    WHERE p.shelter_id = SHELTER.shelter_id
      AND p.status IN ('Reserved', 'Arrived')
)
WHERE shelter_id > 0;   -- key column in WHERE, so MySQL safe update mode accepts it

-- ---------------------------------------------------------------------
-- PART 4: QUERIES USED BY THE APPLICATION
-- ---------------------------------------------------------------------

-- 1.2 Household log in
SELECT ah.member_id, hm.household_id, hm.first_name
FROM ACCOUNT_HOLDER ah
JOIN HOUSEHOLD_MEMBER hm ON hm.member_id = ah.member_id
WHERE ah.login_email = 'anh.nguyen@household.example'
  AND ah.password_hash = 'sample_hash_member_1';

-- 1.3 Staff log in
SELECT staff_id, name
FROM STAFF
WHERE login_email = 'maria.chen@evacbridge.example'
  AND password_hash = 'sample_hash_staff_1';

-- 2.2.1 Notices for the home zone of household 1
SELECT n.notice_id, n.title, n.message, n.published_at
FROM EVACUATION_NOTICE n
JOIN NOTICE_ZONE nz ON nz.notice_id = n.notice_id
JOIN HOUSEHOLD h    ON h.zone_id = nz.zone_id
WHERE h.household_id = 1
ORDER BY n.published_at DESC;

-- 2.2.2 Browse all published notices of an event with their zones
SELECT n.notice_id, n.title, n.published_at, z.zone_name
FROM EVACUATION_NOTICE n
JOIN NOTICE_ZONE nz ON nz.notice_id = n.notice_id
JOIN EVACUATION_ZONE z ON z.zone_id = nz.zone_id
WHERE n.event_id = 1
ORDER BY n.published_at DESC, z.zone_name;

-- 2.3.1 Check whether the household already has a registration for the event
SELECT r.registration_id, r.status, p.placement_no,
       p.status AS placement_status, s.name AS shelter,
       p.arrival_time, p.departure_time
FROM REGISTRATION r
LEFT JOIN PLACEMENT p ON p.registration_id = r.registration_id
    AND p.status IN ('Reserved', 'Arrived')
LEFT JOIN SHELTER s ON s.shelter_id = p.shelter_id
WHERE r.household_id = 5 AND r.event_id = 1;

-- 2.3.2 Open shelters with enough free spaces for 3 participating members
SELECT shelter_id, name, address, available_spaces
FROM SHELTER
WHERE operating_status = 'Open'
AND available_spaces >= 3
AND EXISTS (
SELECT 1
FROM MANAGES
WHERE MANAGES.shelter_id = SHELTER.shelter_id
)
ORDER BY available_spaces DESC;

-- 2.3.5 List registrations for household 1
SELECT registration_id, event_id, status, submitted_at
FROM REGISTRATION
WHERE household_id = 1
ORDER BY submitted_at DESC;

-- 2.3.5 Show placement history for registration 1 in household 1
SELECT PLACEMENT.placement_no,
       SHELTER.name AS shelter_name,
       PLACEMENT.status,
       PLACEMENT.arrival_time,
       PLACEMENT.departure_time
FROM REGISTRATION
JOIN PLACEMENT
    ON PLACEMENT.registration_id = REGISTRATION.registration_id
JOIN SHELTER
    ON SHELTER.shelter_id = PLACEMENT.shelter_id
WHERE REGISTRATION.household_id = 1
  AND REGISTRATION.registration_id = 1
ORDER BY PLACEMENT.placement_no;

-- 2.3.5 Show selected members for registration 1 in household 1
SELECT HOUSEHOLD_MEMBER.member_id,
       HOUSEHOLD_MEMBER.first_name,
       HOUSEHOLD_MEMBER.last_name
FROM REGISTRATION
JOIN REGISTRATION_MEMBER
    ON REGISTRATION_MEMBER.registration_id = REGISTRATION.registration_id
JOIN HOUSEHOLD_MEMBER
    ON HOUSEHOLD_MEMBER.member_id = REGISTRATION_MEMBER.member_id
WHERE REGISTRATION.household_id = 1
  AND REGISTRATION.registration_id = 1
ORDER BY HOUSEHOLD_MEMBER.member_id;

-- 2.4.2 Request status for requester 4
SELECT request_id, sought_person_name, status, staff_response, submitted_at, reviewed_at
FROM REUNIFICATION_REQUEST
WHERE requester_id = 4
ORDER BY submitted_at DESC;

-- 3.4.1 Registrations of event 1 with household contact, member count and placement
SELECT r.registration_id, r.status AS registration_status, h.household_id,
       CONCAT(contact.first_name, ' ', contact.last_name) AS contact_name,
       ah.login_email AS contact_email, contact.phone_number AS contact_phone,
       (SELECT COUNT(*) FROM REGISTRATION_MEMBER rm WHERE rm.registration_id = r.registration_id) AS members,
       p.placement_no, p.status AS placement_status, s.name AS shelter
FROM REGISTRATION r
JOIN HOUSEHOLD h ON h.household_id = r.household_id
LEFT JOIN ACCOUNT_HOLDER ah ON ah.member_id = r.submitter_id
LEFT JOIN HOUSEHOLD_MEMBER contact ON contact.member_id = ah.member_id
JOIN PLACEMENT p ON p.registration_id = r.registration_id
JOIN SHELTER s   ON s.shelter_id = p.shelter_id
WHERE r.event_id = 1
  AND p.status IN ('Reserved', 'Arrived')
ORDER BY s.name, r.registration_id;

-- 3.4.1 Current occupants of shelter 2
SELECT hm.member_id, hm.first_name, hm.last_name, p.status
FROM PLACEMENT p
JOIN REGISTRATION_MEMBER rm ON rm.registration_id = p.registration_id
JOIN HOUSEHOLD_MEMBER hm    ON hm.member_id = rm.member_id
WHERE p.shelter_id = 2 AND p.status = 'Arrived'
ORDER BY hm.last_name, hm.first_name;

-- 3.5.1 Pending reunification requests of event 1
SELECT request_id, sought_person_name, sought_person_dob, other_info, submitted_at
FROM REUNIFICATION_REQUEST
WHERE event_id = 1 AND status = 'Pending'
ORDER BY submitted_at;

-- 3.5.2 Staff search for registered members by name (to find possible matches)
SELECT hm.member_id, hm.first_name, hm.last_name, r.registration_id, p.placement_no, p.status
FROM HOUSEHOLD_MEMBER hm
JOIN REGISTRATION_MEMBER rm ON rm.member_id = hm.member_id
JOIN REGISTRATION r         ON r.registration_id = rm.registration_id
JOIN PLACEMENT p            ON p.registration_id = r.registration_id
WHERE hm.last_name LIKE 'Kowalsk%' AND r.event_id = 1;

-- 3.5.2 Possible matches saved for request 1 (staff only)
SELECT pm.request_id, pm.registration_id, pm.placement_no, p.status, s.name AS shelter
FROM POSSIBLE_MATCH pm
JOIN PLACEMENT p ON p.registration_id = pm.registration_id AND p.placement_no = pm.placement_no
JOIN SHELTER s   ON s.shelter_id = p.shelter_id
WHERE pm.request_id = 1;

-- ---------------------------------------------------------------------
-- PART 5: RULE CHECKS (each query should return no rows)
-- These rules cannot be written as plain table constraints.
-- ---------------------------------------------------------------------

-- Every household has at least one account holder
SELECT h.household_id
FROM HOUSEHOLD h
WHERE NOT EXISTS (
    SELECT 1 FROM HOUSEHOLD_MEMBER hm
    JOIN ACCOUNT_HOLDER ah ON ah.member_id = hm.member_id
    WHERE hm.household_id = h.household_id);

-- Every member in a registration belongs to the registration's household
SELECT rm.registration_id, rm.member_id
FROM REGISTRATION_MEMBER rm
JOIN REGISTRATION r      ON r.registration_id = rm.registration_id
JOIN HOUSEHOLD_MEMBER hm ON hm.member_id = rm.member_id
WHERE hm.household_id <> r.household_id;

-- At most one active placement for each registration
SELECT registration_id, COUNT(*) AS active_placements
FROM PLACEMENT
WHERE status IN ('Reserved', 'Arrived')
GROUP BY registration_id
HAVING COUNT(*) > 1;

-- Active placements only at open shelters that have at least one staff member
SELECT p.registration_id, p.placement_no, p.shelter_id
FROM PLACEMENT p
JOIN SHELTER s ON s.shelter_id = p.shelter_id
WHERE p.status IN ('Reserved', 'Arrived')
  AND (s.operating_status <> 'Open'
       OR NOT EXISTS (SELECT 1 FROM MANAGES m WHERE m.shelter_id = s.shelter_id));

-- Cancelled registrations have no active placement
SELECT r.registration_id
FROM REGISTRATION r
JOIN PLACEMENT p ON p.registration_id = r.registration_id
WHERE r.status = 'Cancelled' AND p.status IN ('Reserved', 'Arrived');

-- available_spaces matches the real number of occupied places
SELECT s.shelter_id, s.available_spaces,
       s.capacity - (SELECT COUNT(*)
                     FROM PLACEMENT p
                     JOIN REGISTRATION_MEMBER rm ON rm.registration_id = p.registration_id
                     WHERE p.shelter_id = s.shelter_id
                       AND p.status IN ('Reserved', 'Arrived')) AS expected_spaces
FROM SHELTER s
WHERE s.available_spaces <> s.capacity - (SELECT COUNT(*)
                     FROM PLACEMENT p
                     JOIN REGISTRATION_MEMBER rm ON rm.registration_id = p.registration_id
                     WHERE p.shelter_id = s.shelter_id
                       AND p.status IN ('Reserved', 'Arrived'));