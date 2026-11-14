-- ============================================================
-- BUSGO - Online Bus Ticket Booking Platform
-- Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS busgo_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE busgo_db;

-- ============================================================
-- DROP TABLES (reverse FK dependency order)
-- ============================================================
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS cancellations;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS passengers;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS seat_availability;
DROP TABLE IF EXISTS seats;
DROP TABLE IF EXISTS schedules;
DROP TABLE IF EXISTS bus_stops;
DROP TABLE IF EXISTS routes;
DROP TABLE IF EXISTS buses;
DROP TABLE IF EXISTS operators;
DROP TABLE IF EXISTS coupons;
DROP TABLE IF EXISTS users;

-- ============================================================
-- TABLE: users
-- ============================================================
CREATE TABLE users (
    user_id    INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(150) NOT NULL,
    phone      VARCHAR(15)  NOT NULL,
    password   VARCHAR(255) NOT NULL,
    role       ENUM('customer','operator','admin') NOT NULL DEFAULT 'customer',
    is_active  TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_users_email (email),
    UNIQUE KEY uq_users_phone (phone),
    INDEX idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: operators
-- ============================================================
CREATE TABLE operators (
    operator_id    INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NOT NULL,
    company_name   VARCHAR(150) NOT NULL,
    email          VARCHAR(150) NOT NULL,
    phone          VARCHAR(15)  NOT NULL,
    license_number VARCHAR(100) NULL,
    address        TEXT         NULL,
    status         ENUM('pending','approved','rejected','suspended') NOT NULL DEFAULT 'pending',
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_operators_email (email),
    UNIQUE KEY uq_operators_license (license_number),
    INDEX idx_operators_user (user_id),
    INDEX idx_operators_status (status),
    CONSTRAINT fk_operators_user FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: buses
-- ============================================================
CREATE TABLE buses (
    bus_id      INT AUTO_INCREMENT PRIMARY KEY,
    operator_id INT NOT NULL,
    bus_name    VARCHAR(150) NOT NULL,
    bus_number  VARCHAR(50)  NOT NULL,
    bus_type    ENUM('AC_SEATER','AC_SLEEPER','NON_AC_SEATER','NON_AC_SLEEPER') NOT NULL,
    total_seats INT NOT NULL DEFAULT 40,
    amenities   TEXT NULL,
    description TEXT NULL,
    rating      DECIMAL(2,1) NOT NULL DEFAULT 0.0,
    is_active   TINYINT(1) NOT NULL DEFAULT 1,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_buses_number (bus_number),
    INDEX idx_buses_operator (operator_id),
    INDEX idx_buses_type (bus_type),
    CONSTRAINT fk_buses_operator FOREIGN KEY (operator_id) REFERENCES operators (operator_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: routes
-- ============================================================
CREATE TABLE routes (
    route_id         INT AUTO_INCREMENT PRIMARY KEY,
    source_city      VARCHAR(100) NOT NULL,
    destination_city VARCHAR(100) NOT NULL,
    distance_km      INT NULL,
    duration_minutes INT NULL,
    is_active        TINYINT(1) NOT NULL DEFAULT 1,
    UNIQUE KEY unique_route (source_city, destination_city),
    INDEX idx_routes_source (source_city),
    INDEX idx_routes_destination (destination_city)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: bus_stops
-- ============================================================
CREATE TABLE bus_stops (
    stop_id        INT AUTO_INCREMENT PRIMARY KEY,
    route_id       INT NOT NULL,
    stop_name      VARCHAR(150) NOT NULL,
    stop_type      ENUM('boarding','dropping','both') NOT NULL DEFAULT 'both',
    sequence_order INT NOT NULL,
    landmark       TEXT NULL,
    INDEX idx_bus_stops_route (route_id),
    INDEX idx_bus_stops_sequence (route_id, sequence_order),
    CONSTRAINT fk_bus_stops_route FOREIGN KEY (route_id) REFERENCES routes (route_id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: schedules
-- ============================================================
CREATE TABLE schedules (
    schedule_id     INT AUTO_INCREMENT PRIMARY KEY,
    bus_id          INT NOT NULL,
    route_id        INT NOT NULL,
    journey_date    DATE NOT NULL,
    departure_time  TIME NOT NULL,
    arrival_time    TIME NOT NULL,
    ticket_price    DECIMAL(10,2) NOT NULL,
    available_seats INT NOT NULL,
    status          ENUM('scheduled','cancelled','completed') NOT NULL DEFAULT 'scheduled',
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_route_date (route_id, journey_date),
    INDEX idx_bus_date (bus_id, journey_date),
    INDEX idx_schedules_status (status),
    CONSTRAINT fk_schedules_bus FOREIGN KEY (bus_id) REFERENCES buses (bus_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_schedules_route FOREIGN KEY (route_id) REFERENCES routes (route_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: seats
-- ============================================================
CREATE TABLE seats (
    seat_id        INT AUTO_INCREMENT PRIMARY KEY,
    bus_id         INT NOT NULL,
    seat_number    VARCHAR(10) NOT NULL,
    seat_type      ENUM('seater','lower_berth','upper_berth') NOT NULL,
    deck           ENUM('lower','upper','single') NOT NULL DEFAULT 'single',
    is_female_only TINYINT(1) NOT NULL DEFAULT 0,
    UNIQUE KEY unique_seat (bus_id, seat_number),
    INDEX idx_seats_bus (bus_id),
    CONSTRAINT fk_seats_bus FOREIGN KEY (bus_id) REFERENCES buses (bus_id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: seat_availability
-- ============================================================
CREATE TABLE seat_availability (
    availability_id INT AUTO_INCREMENT PRIMARY KEY,
    seat_id         INT NOT NULL,
    schedule_id     INT NOT NULL,
    status          ENUM('available','booked','locked','blocked') NOT NULL DEFAULT 'available',
    locked_until    TIMESTAMP NULL,
    locked_by       INT NULL,
    UNIQUE KEY unique_seat_schedule (seat_id, schedule_id),
    INDEX idx_schedule_status (schedule_id, status),
    INDEX idx_seat_availability_seat (seat_id),
    CONSTRAINT fk_seat_avail_seat FOREIGN KEY (seat_id) REFERENCES seats (seat_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_seat_avail_schedule FOREIGN KEY (schedule_id) REFERENCES schedules (schedule_id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: bookings
-- ============================================================
CREATE TABLE bookings (
    booking_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL,
    schedule_id      INT NOT NULL,
    booking_date     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount     DECIMAL(10,2) NOT NULL,
    convenience_fee  DECIMAL(10,2) NOT NULL DEFAULT 0,
    taxes            DECIMAL(10,2) NOT NULL DEFAULT 0,
    discount_amount  DECIMAL(10,2) NOT NULL DEFAULT 0,
    booking_status   ENUM('pending','confirmed','cancelled','failed') NOT NULL DEFAULT 'pending',
    pnr_number       VARCHAR(20)  NOT NULL,
    boarding_stop_id INT NULL,
    dropping_stop_id INT NULL,
    coupon_code      VARCHAR(50)  NULL,
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_bookings_pnr (pnr_number),
    INDEX idx_bookings_user (user_id),
    INDEX idx_bookings_schedule (schedule_id),
    INDEX idx_bookings_status (booking_status),
    CONSTRAINT fk_bookings_user FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_bookings_schedule FOREIGN KEY (schedule_id) REFERENCES schedules (schedule_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: passengers
-- ============================================================
CREATE TABLE passengers (
    passenger_id   INT AUTO_INCREMENT PRIMARY KEY,
    booking_id     INT NOT NULL,
    passenger_name VARCHAR(100) NOT NULL,
    age            INT NOT NULL,
    gender         ENUM('male','female','other') NOT NULL,
    seat_id        INT NOT NULL,
    seat_number    VARCHAR(10)  NOT NULL,
    INDEX idx_passengers_booking (booking_id),
    INDEX idx_passengers_seat (seat_id),
    CONSTRAINT fk_passengers_booking FOREIGN KEY (booking_id) REFERENCES bookings (booking_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_passengers_seat FOREIGN KEY (seat_id) REFERENCES seats (seat_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: payments
-- ============================================================
CREATE TABLE payments (
    payment_id          INT AUTO_INCREMENT PRIMARY KEY,
    booking_id          INT NOT NULL,
    razorpay_order_id   VARCHAR(100) NULL,
    razorpay_payment_id VARCHAR(100) NULL,
    razorpay_signature  VARCHAR(255) NULL,
    transaction_id      VARCHAR(100) NULL,
    amount              DECIMAL(10,2) NOT NULL,
    payment_method      VARCHAR(50)   NULL,
    payment_status      ENUM('pending','success','failed','refunded') NOT NULL DEFAULT 'pending',
    payment_date        TIMESTAMP NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_payments_razorpay_order  (razorpay_order_id),
    UNIQUE KEY uq_payments_razorpay_pay    (razorpay_payment_id),
    UNIQUE KEY uq_payments_transaction     (transaction_id),
    INDEX idx_payments_booking (booking_id),
    INDEX idx_payments_status  (payment_status),
    CONSTRAINT fk_payments_booking FOREIGN KEY (booking_id) REFERENCES bookings (booking_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: cancellations
-- ============================================================
CREATE TABLE cancellations (
    cancellation_id      INT AUTO_INCREMENT PRIMARY KEY,
    booking_id           INT NOT NULL,
    cancellation_date    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    refund_amount        DECIMAL(10,2) NOT NULL DEFAULT 0,
    cancellation_charges DECIMAL(10,2) NOT NULL DEFAULT 0,
    refund_status        ENUM('pending','processed','failed') NOT NULL DEFAULT 'pending',
    refund_reference     VARCHAR(100) NULL,
    reason               TEXT NULL,
    processed_at         TIMESTAMP NULL,
    INDEX idx_cancellations_booking (booking_id),
    INDEX idx_cancellations_refund_status (refund_status),
    CONSTRAINT fk_cancellations_booking FOREIGN KEY (booking_id) REFERENCES bookings (booking_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: reviews
-- ============================================================
CREATE TABLE reviews (
    review_id  INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    bus_id     INT NOT NULL,
    booking_id INT NOT NULL,
    rating     INT NOT NULL,
    comments   TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY one_review_per_booking (user_id, booking_id),
    INDEX idx_reviews_bus (bus_id),
    INDEX idx_reviews_user (user_id),
    CONSTRAINT chk_reviews_rating CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT fk_reviews_user FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_reviews_bus FOREIGN KEY (bus_id) REFERENCES buses (bus_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_reviews_booking FOREIGN KEY (booking_id) REFERENCES bookings (booking_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: coupons
-- ============================================================
CREATE TABLE coupons (
    coupon_id          INT AUTO_INCREMENT PRIMARY KEY,
    code               VARCHAR(50)   NOT NULL,
    discount_type      ENUM('percentage','fixed') NOT NULL,
    discount_value     DECIMAL(10,2) NOT NULL,
    min_booking_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    max_discount       DECIMAL(10,2) NULL,
    valid_from         DATE NULL,
    valid_until        DATE NULL,
    usage_limit        INT NOT NULL DEFAULT 100,
    used_count         INT NOT NULL DEFAULT 0,
    is_active          TINYINT(1) NOT NULL DEFAULT 1,
    UNIQUE KEY uq_coupons_code (code),
    INDEX idx_coupons_active (is_active),
    INDEX idx_coupons_valid (valid_from, valid_until)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- END OF SCHEMA
-- ============================================================
