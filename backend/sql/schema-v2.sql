CREATE TABLE EVACUATION_ZONE (
    zone_id INT NOT NULL AUTO_INCREMENT,
    zone_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (zone_id)
);

CREATE TABLE EMERGENCY_EVENT (
    event_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    event_type VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    PRIMARY KEY (event_id),
    CONSTRAINT chk_event_type   CHECK (event_type IN ('Wildfire', 'Flood')),
    CONSTRAINT chk_event_status CHECK (status IN ('Active', 'Closed')),
    CONSTRAINT chk_event_dates  CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE STAFF (
    staff_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    login_email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    PRIMARY KEY (staff_id),
    UNIQUE (login_email)
);

CREATE TABLE HOUSEHOLD (
    household_id INT NOT NULL AUTO_INCREMENT,
    street VARCHAR(100) NOT NULL,
    city VARCHAR(60) NOT NULL,
    province VARCHAR(30) NOT NULL,
    postal_code VARCHAR(10) NOT NULL,
    zone_id INT NOT NULL,
    PRIMARY KEY (household_id),
    FOREIGN KEY (zone_id)
        REFERENCES EVACUATION_ZONE (zone_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE HOUSEHOLD_MEMBER (
    member_id INT NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    phone_number VARCHAR(20) NULL,
    household_id INT NOT NULL,
    PRIMARY KEY (member_id),
    FOREIGN KEY (household_id)
        REFERENCES HOUSEHOLD (household_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE ACCOUNT_HOLDER (
    member_id INT NOT NULL,
    login_email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    PRIMARY KEY (member_id),
    UNIQUE (login_email),
    FOREIGN KEY (member_id)
        REFERENCES HOUSEHOLD_MEMBER (member_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE EVACUATION_NOTICE (
    notice_id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    published_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_id INT NOT NULL,
    staff_id INT NOT NULL,
    PRIMARY KEY (notice_id),
    FOREIGN KEY (event_id)
        REFERENCES EMERGENCY_EVENT (event_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (staff_id)
        REFERENCES STAFF (staff_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE NOTICE_ZONE (
    notice_id INT NOT NULL,
    zone_id INT NOT NULL,
    PRIMARY KEY (notice_id, zone_id),
    FOREIGN KEY (notice_id)
        REFERENCES EVACUATION_NOTICE (notice_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (zone_id)
        REFERENCES EVACUATION_ZONE (zone_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE REGISTRATION (
    registration_id INT NOT NULL AUTO_INCREMENT,
    submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    household_id INT NOT NULL,
    event_id INT NOT NULL,
    submitter_id INT NULL,
    PRIMARY KEY (registration_id),
    UNIQUE (household_id, event_id),
    CONSTRAINT chk_registration_status CHECK (status IN ('Active', 'Cancelled')),
    FOREIGN KEY (household_id)
        REFERENCES HOUSEHOLD (household_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (event_id)
        REFERENCES EMERGENCY_EVENT (event_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (submitter_id)
        REFERENCES ACCOUNT_HOLDER (member_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE REGISTRATION_MEMBER (
    registration_id INT NOT NULL,
    member_id INT NOT NULL,
    PRIMARY KEY (registration_id, member_id),
    FOREIGN KEY (registration_id)
        REFERENCES REGISTRATION (registration_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (member_id)
        REFERENCES HOUSEHOLD_MEMBER (member_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE SHELTER (
    shelter_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(150) NOT NULL,
    capacity INT NOT NULL,
    operating_status VARCHAR(20) NOT NULL DEFAULT 'Open',
    available_spaces INT NOT NULL,
    PRIMARY KEY (shelter_id),
    CONSTRAINT chk_shelter_capacity CHECK (capacity > 0),
    CONSTRAINT chk_shelter_status   CHECK (operating_status IN ('Open', 'Closed')),
    CONSTRAINT chk_shelter_spaces   CHECK (available_spaces >= 0 AND available_spaces <= capacity)
);

CREATE TABLE MANAGES (
    staff_id INT NOT NULL,
    shelter_id INT NOT NULL,
    PRIMARY KEY (staff_id, shelter_id),
    FOREIGN KEY (staff_id)
        REFERENCES STAFF (staff_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (shelter_id)
        REFERENCES SHELTER (shelter_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE PLACEMENT (
    registration_id INT NOT NULL,
    placement_no INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    arrival_time DATETIME NULL,
    departure_time DATETIME NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Reserved',
    shelter_id INT NOT NULL,
    PRIMARY KEY (registration_id, placement_no),
    CONSTRAINT chk_placement_no     CHECK (placement_no >= 1),
    CONSTRAINT chk_placement_status CHECK (status IN ('Reserved', 'Arrived', 'Departed', 'Transferred', 'Cancelled')),
    CONSTRAINT chk_placement_times  CHECK (arrival_time IS NULL OR departure_time IS NULL OR departure_time >= arrival_time),
    FOREIGN KEY (registration_id)
        REFERENCES REGISTRATION (registration_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (shelter_id)
        REFERENCES SHELTER (shelter_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE REUNIFICATION_REQUEST (
    request_id INT NOT NULL AUTO_INCREMENT,
    sought_person_name VARCHAR(100) NOT NULL,
    sought_person_dob DATE NULL,
    other_info VARCHAR(255) NULL,
    submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    staff_response TEXT NULL,
    reviewed_at DATETIME NULL,
    event_id INT NOT NULL,
    requester_id INT NOT NULL,
    reviewer_id INT NULL,
    PRIMARY KEY (request_id),
    CONSTRAINT chk_request_status CHECK (status IN ('Pending', 'Responded')),
    CONSTRAINT chk_request_review CHECK (reviewed_at IS NULL OR reviewed_at >= submitted_at),
    CONSTRAINT chk_request_responded CHECK (status = 'Pending' OR (staff_response IS NOT NULL AND reviewed_at IS NOT NULL)),
    FOREIGN KEY (event_id)
        REFERENCES EMERGENCY_EVENT (event_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (requester_id)
        REFERENCES ACCOUNT_HOLDER (member_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (reviewer_id)
        REFERENCES STAFF (staff_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE POSSIBLE_MATCH (
    request_id INT NOT NULL,
    registration_id INT NOT NULL,
    placement_no INT NOT NULL,
    PRIMARY KEY (request_id, registration_id, placement_no),
    FOREIGN KEY (request_id)
        REFERENCES REUNIFICATION_REQUEST (request_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (registration_id, placement_no)
        REFERENCES PLACEMENT (registration_id, placement_no)
        ON DELETE CASCADE ON UPDATE CASCADE
);
