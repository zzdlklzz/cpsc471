-- EvacBridge: MySQL initial schema.
-- Select an empty database with USE before running this file.
-- Based on the finalized RM/EERD, excluding REUNIFICATION_REQUEST and
-- POSSIBLE_MATCH. No other relations or attributes are removed.
-- Run once: this is not a migration or a database reset script.
-- Status vocabularies and cross-table business rules belong to the shared
-- feature procedures/transactions; see README.md in this directory.

-- Accounts and households
CREATE TABLE EVACUATION_ZONE (
    zone_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    zone_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (zone_id)
);

CREATE TABLE HOUSEHOLD (
    household_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    street VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    province VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    zone_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (household_id),
    FOREIGN KEY (zone_id) REFERENCES EVACUATION_ZONE (zone_id)
);

CREATE TABLE HOUSEHOLD_MEMBER (
    member_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    phone_number VARCHAR(30) NULL,
    household_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (member_id),
    FOREIGN KEY (household_id) REFERENCES HOUSEHOLD (household_id)
);

CREATE TABLE ACCOUNT_HOLDER (
    member_id INT UNSIGNED NOT NULL,
    login_email VARCHAR(254) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    PRIMARY KEY (member_id),
    UNIQUE (login_email),
    FOREIGN KEY (member_id) REFERENCES HOUSEHOLD_MEMBER (member_id)
);

CREATE TABLE STAFF (
    staff_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    login_email VARCHAR(254) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    PRIMARY KEY (staff_id),
    UNIQUE (login_email)
);

-- Events and notices
CREATE TABLE EMERGENCY_EVENT (
    event_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    status VARCHAR(30) NOT NULL,
    PRIMARY KEY (event_id),
    CONSTRAINT chk_event_dates CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE EVACUATION_NOTICE (
    notice_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    published_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_id INT UNSIGNED NOT NULL,
    staff_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (notice_id),
    FOREIGN KEY (event_id) REFERENCES EMERGENCY_EVENT (event_id),
    FOREIGN KEY (staff_id) REFERENCES STAFF (staff_id)
);

CREATE TABLE NOTICE_ZONE (
    notice_id INT UNSIGNED NOT NULL,
    zone_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (notice_id, zone_id),
    FOREIGN KEY (notice_id) REFERENCES EVACUATION_NOTICE (notice_id),
    FOREIGN KEY (zone_id) REFERENCES EVACUATION_ZONE (zone_id)
);

-- Shelter settings and staff assignments
CREATE TABLE SHELTER (
    shelter_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    address VARCHAR(255) NOT NULL,
    capacity INT NOT NULL,
    operating_status VARCHAR(30) NOT NULL,
    available_spaces INT NOT NULL,
    PRIMARY KEY (shelter_id),
    CONSTRAINT chk_shelter_capacity CHECK (capacity >= 0),
    CONSTRAINT chk_shelter_availability
        CHECK (available_spaces >= 0 AND available_spaces <= capacity)
);

CREATE TABLE MANAGES (
    staff_id INT UNSIGNED NOT NULL,
    shelter_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (staff_id, shelter_id),
    FOREIGN KEY (staff_id) REFERENCES STAFF (staff_id),
    FOREIGN KEY (shelter_id) REFERENCES SHELTER (shelter_id)
);

-- Household registrations, participants, and placement history
CREATE TABLE REGISTRATION (
    registration_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) NOT NULL,
    household_id INT UNSIGNED NOT NULL,
    event_id INT UNSIGNED NOT NULL,
    submitter_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (registration_id),
    UNIQUE (household_id, event_id),
    FOREIGN KEY (household_id) REFERENCES HOUSEHOLD (household_id),
    FOREIGN KEY (event_id) REFERENCES EMERGENCY_EVENT (event_id),
    FOREIGN KEY (submitter_id) REFERENCES ACCOUNT_HOLDER (member_id)
);

CREATE TABLE REGISTRATION_MEMBER (
    registration_id INT UNSIGNED NOT NULL,
    member_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (registration_id, member_id),
    FOREIGN KEY (registration_id) REFERENCES REGISTRATION (registration_id),
    FOREIGN KEY (member_id) REFERENCES HOUSEHOLD_MEMBER (member_id)
);

CREATE TABLE PLACEMENT (
    registration_id INT UNSIGNED NOT NULL,
    placement_no INT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    arrival_time DATETIME NULL,
    departure_time DATETIME NULL,
    status VARCHAR(30) NOT NULL,
    shelter_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (registration_id, placement_no),
    FOREIGN KEY (registration_id) REFERENCES REGISTRATION (registration_id),
    FOREIGN KEY (shelter_id) REFERENCES SHELTER (shelter_id),
    CONSTRAINT chk_placement_number CHECK (placement_no > 0),
    CONSTRAINT chk_placement_times CHECK (
        departure_time IS NULL
        OR (arrival_time IS NOT NULL AND departure_time >= arrival_time)
    )
);
