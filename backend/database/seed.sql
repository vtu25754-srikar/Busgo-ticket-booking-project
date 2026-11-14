-- ============================================================
-- BUSGO - Online Bus Ticket Booking Platform
-- Seed Data
-- ============================================================

USE busgo_db;

-- ============================================================
-- USERS
-- ============================================================
INSERT INTO users (name, email, phone, password, role) VALUES
('Admin User',       'admin@busgo.com',    '9000000000', '$2a$10$placeholder_hash', 'admin'),
('Sharma Operator',  'sharma@busgo.com',   '9100000001', '$2a$10$placeholder_hash', 'operator'),
('Redline Operator', 'redline@busgo.com',  '9100000002', '$2a$10$placeholder_hash', 'operator');

-- ============================================================
-- OPERATORS
-- ============================================================
INSERT INTO operators (user_id, company_name, email, phone, license_number, address, status) VALUES
(2, 'Sharma Travels',   'sharma@busgo.com',  '9100000001', 'LIC-SHARMA-001', '12, MG Road, Hyderabad, Telangana', 'approved'),
(3, 'RedLine Express',  'redline@busgo.com', '9100000002', 'LIC-REDLINE-002', '45, Anna Salai, Chennai, Tamil Nadu', 'approved');

-- ============================================================
-- BUSES
-- ============================================================
INSERT INTO buses (operator_id, bus_name, bus_number, bus_type, total_seats, amenities, description, rating) VALUES
(1, 'Sharma Volvo AC',  'TS09EA1234', 'AC_SLEEPER',     40, 'WiFi, Charging Point, Blanket, Water Bottle', 'Luxurious Volvo AC Sleeper with premium amenities', 4.5),
(1, 'Sharma Express',   'TS09EB5678', 'NON_AC_SEATER',  45, 'Charging Point, Water Bottle',                 'Comfortable non-AC seater for budget travellers',  3.8),
(2, 'RedLine Premium',  'TN07AC9012', 'AC_SEATER',      40, 'WiFi, Charging Point, Snacks',                 'Premium AC seater with extra legroom',              4.2),
(2, 'RedLine Sleeper',  'TN07AD3456', 'NON_AC_SLEEPER', 40, 'Blanket, Pillow, Charging Point',              'Affordable non-AC sleeper for overnight journeys',  3.9);

-- ============================================================
-- ROUTES
-- ============================================================
INSERT INTO routes (source_city, destination_city, distance_km, duration_minutes) VALUES
('Hyderabad', 'Bangalore', 570, 540),
('Hyderabad', 'Mumbai',    710, 720),
('Delhi',     'Jaipur',    280, 300),
('Chennai',   'Bangalore', 350, 360),
('Mumbai',    'Pune',      150, 180);

-- ============================================================
-- BUS STOPS
-- Route 1: Hyderabad → Bangalore
-- ============================================================
INSERT INTO bus_stops (route_id, stop_name, stop_type, sequence_order, landmark) VALUES
-- Hyderabad → Bangalore (route_id=1)
(1, 'Majestic Bus Stand, Hyderabad',  'boarding', 1, 'Near Hyderabad Central Railway Station'),
(1, 'Kurnool Bus Station',            'both',     2, 'Opposite Kurnool Court'),
(1, 'Anantapur Bus Stand',            'both',     3, 'Near Anantapur Clock Tower'),
(1, 'Majestic Bus Stand, Bangalore',  'dropping', 4, 'Opposite Bangalore City Railway Station'),

-- Hyderabad → Mumbai (route_id=2)
(2, 'Jubilee Bus Station, Hyderabad', 'boarding', 1, 'Near Secunderabad Railway Station'),
(2, 'Solapur Bus Stand',              'both',     2, 'Near Solapur Railway Station'),
(2, 'Pune Bus Depot',                 'both',     3, 'Swargate, Pune'),
(2, 'Mumbai Central Bus Terminus',    'dropping', 4, 'Near Mumbai Central Railway Station'),

-- Delhi → Jaipur (route_id=3)
(3, 'Kashmere Gate ISBT, Delhi',      'boarding', 1, 'Near Kashmere Gate Metro Station'),
(3, 'Behror Toll Plaza',              'both',     2, 'NH48, Behror'),
(3, 'Shahpura',                       'both',     3, 'Shahpura Bus Stand'),
(3, 'Sindhi Camp Bus Stand, Jaipur',  'dropping', 4, 'Near Jaipur Railway Station'),

-- Chennai → Bangalore (route_id=4)
(4, 'Koyambedu Bus Terminus, Chennai','boarding', 1, 'CMBT, Koyambedu'),
(4, 'Krishnagiri Bus Stand',          'both',     2, 'Near Krishnagiri Town'),
(4, 'Hosur Bus Stand',                'both',     3, 'Hosur Town, Tamil Nadu'),
(4, 'Majestic Bus Stand, Bangalore',  'dropping', 4, 'Opposite Bangalore City Railway Station'),

-- Mumbai → Pune (route_id=5)
(5, 'Mumbai Central Bus Terminus',    'boarding', 1, 'Near Mumbai Central Railway Station'),
(5, 'Khopoli',                        'both',     2, 'Near Expressway Toll'),
(5, 'Swargate Bus Stand, Pune',       'dropping', 3, 'Swargate, Pune');

-- ============================================================
-- SEATS – Bus 1 (AC_SLEEPER, 40 seats: L1–L20 lower, U1–U20 upper)
-- ============================================================
INSERT INTO seats (bus_id, seat_number, seat_type, deck, is_female_only) VALUES
-- Lower berths
(1,'L1',  'lower_berth','lower',0),(1,'L2',  'lower_berth','lower',0),
(1,'L3',  'lower_berth','lower',0),(1,'L4',  'lower_berth','lower',0),
(1,'L5',  'lower_berth','lower',1),(1,'L6',  'lower_berth','lower',1),
(1,'L7',  'lower_berth','lower',0),(1,'L8',  'lower_berth','lower',0),
(1,'L9',  'lower_berth','lower',0),(1,'L10', 'lower_berth','lower',0),
(1,'L11', 'lower_berth','lower',0),(1,'L12', 'lower_berth','lower',0),
(1,'L13', 'lower_berth','lower',0),(1,'L14', 'lower_berth','lower',0),
(1,'L15', 'lower_berth','lower',0),(1,'L16', 'lower_berth','lower',0),
(1,'L17', 'lower_berth','lower',0),(1,'L18', 'lower_berth','lower',0),
(1,'L19', 'lower_berth','lower',0),(1,'L20', 'lower_berth','lower',0),
-- Upper berths
(1,'U1',  'upper_berth','upper',0),(1,'U2',  'upper_berth','upper',0),
(1,'U3',  'upper_berth','upper',0),(1,'U4',  'upper_berth','upper',0),
(1,'U5',  'upper_berth','upper',0),(1,'U6',  'upper_berth','upper',0),
(1,'U7',  'upper_berth','upper',0),(1,'U8',  'upper_berth','upper',0),
(1,'U9',  'upper_berth','upper',0),(1,'U10', 'upper_berth','upper',0),
(1,'U11', 'upper_berth','upper',0),(1,'U12', 'upper_berth','upper',0),
(1,'U13', 'upper_berth','upper',0),(1,'U14', 'upper_berth','upper',0),
(1,'U15', 'upper_berth','upper',0),(1,'U16', 'upper_berth','upper',0),
(1,'U17', 'upper_berth','upper',0),(1,'U18', 'upper_berth','upper',0),
(1,'U19', 'upper_berth','upper',0),(1,'U20', 'upper_berth','upper',0);

-- ============================================================
-- SEATS – Bus 2 (NON_AC_SEATER, 45 seats: A1–A45)
-- ============================================================
INSERT INTO seats (bus_id, seat_number, seat_type, deck, is_female_only) VALUES
(2,'A1', 'seater','single',0),(2,'A2', 'seater','single',0),(2,'A3', 'seater','single',0),
(2,'A4', 'seater','single',0),(2,'A5', 'seater','single',0),(2,'A6', 'seater','single',0),
(2,'A7', 'seater','single',0),(2,'A8', 'seater','single',0),(2,'A9', 'seater','single',0),
(2,'A10','seater','single',0),(2,'A11','seater','single',0),(2,'A12','seater','single',0),
(2,'A13','seater','single',0),(2,'A14','seater','single',0),(2,'A15','seater','single',1),
(2,'A16','seater','single',1),(2,'A17','seater','single',1),(2,'A18','seater','single',0),
(2,'A19','seater','single',0),(2,'A20','seater','single',0),(2,'A21','seater','single',0),
(2,'A22','seater','single',0),(2,'A23','seater','single',0),(2,'A24','seater','single',0),
(2,'A25','seater','single',0),(2,'A26','seater','single',0),(2,'A27','seater','single',0),
(2,'A28','seater','single',0),(2,'A29','seater','single',0),(2,'A30','seater','single',0),
(2,'A31','seater','single',0),(2,'A32','seater','single',0),(2,'A33','seater','single',0),
(2,'A34','seater','single',0),(2,'A35','seater','single',0),(2,'A36','seater','single',0),
(2,'A37','seater','single',0),(2,'A38','seater','single',0),(2,'A39','seater','single',0),
(2,'A40','seater','single',0),(2,'A41','seater','single',0),(2,'A42','seater','single',0),
(2,'A43','seater','single',0),(2,'A44','seater','single',0),(2,'A45','seater','single',0);

-- ============================================================
-- SCHEDULES
-- Bus 1 (AC_SLEEPER) → Route 1 (Hyderabad-Bangalore), 7 days
-- Bus 2 (NON_AC_SEATER) → Route 1 (Hyderabad-Bangalore), 7 days
-- Bus 3 (AC_SEATER) → Route 4 (Chennai-Bangalore), 7 days
-- Bus 4 (NON_AC_SLEEPER) → Route 2 (Hyderabad-Mumbai), 7 days
-- ============================================================
INSERT INTO schedules (bus_id, route_id, journey_date, departure_time, arrival_time, ticket_price, available_seats) VALUES
-- Bus 1, Route 1, days 1-7
(1,1,DATE_ADD(CURDATE(),INTERVAL 1 DAY),'21:00:00','06:00:00',1200.00,40),
(1,1,DATE_ADD(CURDATE(),INTERVAL 2 DAY),'21:00:00','06:00:00',1200.00,40),
(1,1,DATE_ADD(CURDATE(),INTERVAL 3 DAY),'21:00:00','06:00:00',1200.00,40),
(1,1,DATE_ADD(CURDATE(),INTERVAL 4 DAY),'21:00:00','06:00:00',1200.00,40),
(1,1,DATE_ADD(CURDATE(),INTERVAL 5 DAY),'21:00:00','06:00:00',1200.00,40),
(1,1,DATE_ADD(CURDATE(),INTERVAL 6 DAY),'21:00:00','06:00:00',1200.00,40),
(1,1,DATE_ADD(CURDATE(),INTERVAL 7 DAY),'21:00:00','06:00:00',1200.00,40),
-- Bus 2, Route 1, days 1-7
(2,1,DATE_ADD(CURDATE(),INTERVAL 1 DAY),'08:00:00','17:00:00', 650.00,45),
(2,1,DATE_ADD(CURDATE(),INTERVAL 2 DAY),'08:00:00','17:00:00', 650.00,45),
(2,1,DATE_ADD(CURDATE(),INTERVAL 3 DAY),'08:00:00','17:00:00', 650.00,45),
(2,1,DATE_ADD(CURDATE(),INTERVAL 4 DAY),'08:00:00','17:00:00', 650.00,45),
(2,1,DATE_ADD(CURDATE(),INTERVAL 5 DAY),'08:00:00','17:00:00', 650.00,45),
(2,1,DATE_ADD(CURDATE(),INTERVAL 6 DAY),'08:00:00','17:00:00', 650.00,45),
(2,1,DATE_ADD(CURDATE(),INTERVAL 7 DAY),'08:00:00','17:00:00', 650.00,45),
-- Bus 3, Route 4 (Chennai-Bangalore), days 1-7
(3,4,DATE_ADD(CURDATE(),INTERVAL 1 DAY),'06:00:00','12:00:00', 850.00,40),
(3,4,DATE_ADD(CURDATE(),INTERVAL 2 DAY),'06:00:00','12:00:00', 850.00,40),
(3,4,DATE_ADD(CURDATE(),INTERVAL 3 DAY),'06:00:00','12:00:00', 850.00,40),
(3,4,DATE_ADD(CURDATE(),INTERVAL 4 DAY),'06:00:00','12:00:00', 850.00,40),
(3,4,DATE_ADD(CURDATE(),INTERVAL 5 DAY),'06:00:00','12:00:00', 850.00,40),
(3,4,DATE_ADD(CURDATE(),INTERVAL 6 DAY),'06:00:00','12:00:00', 850.00,40),
(3,4,DATE_ADD(CURDATE(),INTERVAL 7 DAY),'06:00:00','12:00:00', 850.00,40),
-- Bus 4, Route 2 (Hyderabad-Mumbai), days 1-7
(4,2,DATE_ADD(CURDATE(),INTERVAL 1 DAY),'18:00:00','06:00:00', 950.00,40),
(4,2,DATE_ADD(CURDATE(),INTERVAL 2 DAY),'18:00:00','06:00:00', 950.00,40),
(4,2,DATE_ADD(CURDATE(),INTERVAL 3 DAY),'18:00:00','06:00:00', 950.00,40),
(4,2,DATE_ADD(CURDATE(),INTERVAL 4 DAY),'18:00:00','06:00:00', 950.00,40),
(4,2,DATE_ADD(CURDATE(),INTERVAL 5 DAY),'18:00:00','06:00:00', 950.00,40),
(4,2,DATE_ADD(CURDATE(),INTERVAL 6 DAY),'18:00:00','06:00:00', 950.00,40),
(4,2,DATE_ADD(CURDATE(),INTERVAL 7 DAY),'18:00:00','06:00:00', 950.00,40);

-- ============================================================
-- SEAT AVAILABILITY
-- Bus 1: seats 1-40  × schedules 1-7
-- Bus 2: seats 41-85 × schedules 8-14
-- Bus 3: seats 86-125 × schedules 15-21  (seats for bus 3 not inserted above – covered by operator use)
-- Bus 4: seats 126-165 × schedules 22-28
-- We insert only for the buses whose seats are seeded (bus 1 & 2).
-- ============================================================

-- Bus 1 seats (seat_id 1-40) × schedules 1-7
INSERT INTO seat_availability (seat_id, schedule_id, status) VALUES
-- schedule 1
(1,1,'available'),(2,1,'available'),(3,1,'available'),(4,1,'available'),(5,1,'available'),
(6,1,'available'),(7,1,'available'),(8,1,'available'),(9,1,'available'),(10,1,'available'),
(11,1,'available'),(12,1,'available'),(13,1,'available'),(14,1,'available'),(15,1,'available'),
(16,1,'available'),(17,1,'available'),(18,1,'available'),(19,1,'available'),(20,1,'available'),
(21,1,'available'),(22,1,'available'),(23,1,'available'),(24,1,'available'),(25,1,'available'),
(26,1,'available'),(27,1,'available'),(28,1,'available'),(29,1,'available'),(30,1,'available'),
(31,1,'available'),(32,1,'available'),(33,1,'available'),(34,1,'available'),(35,1,'available'),
(36,1,'available'),(37,1,'available'),(38,1,'available'),(39,1,'available'),(40,1,'available'),
-- schedule 2
(1,2,'available'),(2,2,'available'),(3,2,'available'),(4,2,'available'),(5,2,'available'),
(6,2,'available'),(7,2,'available'),(8,2,'available'),(9,2,'available'),(10,2,'available'),
(11,2,'available'),(12,2,'available'),(13,2,'available'),(14,2,'available'),(15,2,'available'),
(16,2,'available'),(17,2,'available'),(18,2,'available'),(19,2,'available'),(20,2,'available'),
(21,2,'available'),(22,2,'available'),(23,2,'available'),(24,2,'available'),(25,2,'available'),
(26,2,'available'),(27,2,'available'),(28,2,'available'),(29,2,'available'),(30,2,'available'),
(31,2,'available'),(32,2,'available'),(33,2,'available'),(34,2,'available'),(35,2,'available'),
(36,2,'available'),(37,2,'available'),(38,2,'available'),(39,2,'available'),(40,2,'available'),
-- schedule 3
(1,3,'available'),(2,3,'available'),(3,3,'available'),(4,3,'available'),(5,3,'available'),
(6,3,'available'),(7,3,'available'),(8,3,'available'),(9,3,'available'),(10,3,'available'),
(11,3,'available'),(12,3,'available'),(13,3,'available'),(14,3,'available'),(15,3,'available'),
(16,3,'available'),(17,3,'available'),(18,3,'available'),(19,3,'available'),(20,3,'available'),
(21,3,'available'),(22,3,'available'),(23,3,'available'),(24,3,'available'),(25,3,'available'),
(26,3,'available'),(27,3,'available'),(28,3,'available'),(29,3,'available'),(30,3,'available'),
(31,3,'available'),(32,3,'available'),(33,3,'available'),(34,3,'available'),(35,3,'available'),
(36,3,'available'),(37,3,'available'),(38,3,'available'),(39,3,'available'),(40,3,'available'),
-- schedule 4
(1,4,'available'),(2,4,'available'),(3,4,'available'),(4,4,'available'),(5,4,'available'),
(6,4,'available'),(7,4,'available'),(8,4,'available'),(9,4,'available'),(10,4,'available'),
(11,4,'available'),(12,4,'available'),(13,4,'available'),(14,4,'available'),(15,4,'available'),
(16,4,'available'),(17,4,'available'),(18,4,'available'),(19,4,'available'),(20,4,'available'),
(21,4,'available'),(22,4,'available'),(23,4,'available'),(24,4,'available'),(25,4,'available'),
(26,4,'available'),(27,4,'available'),(28,4,'available'),(29,4,'available'),(30,4,'available'),
(31,4,'available'),(32,4,'available'),(33,4,'available'),(34,4,'available'),(35,4,'available'),
(36,4,'available'),(37,4,'available'),(38,4,'available'),(39,4,'available'),(40,4,'available'),
-- schedule 5
(1,5,'available'),(2,5,'available'),(3,5,'available'),(4,5,'available'),(5,5,'available'),
(6,5,'available'),(7,5,'available'),(8,5,'available'),(9,5,'available'),(10,5,'available'),
(11,5,'available'),(12,5,'available'),(13,5,'available'),(14,5,'available'),(15,5,'available'),
(16,5,'available'),(17,5,'available'),(18,5,'available'),(19,5,'available'),(20,5,'available'),
(21,5,'available'),(22,5,'available'),(23,5,'available'),(24,5,'available'),(25,5,'available'),
(26,5,'available'),(27,5,'available'),(28,5,'available'),(29,5,'available'),(30,5,'available'),
(31,5,'available'),(32,5,'available'),(33,5,'available'),(34,5,'available'),(35,5,'available'),
(36,5,'available'),(37,5,'available'),(38,5,'available'),(39,5,'available'),(40,5,'available'),
-- schedule 6
(1,6,'available'),(2,6,'available'),(3,6,'available'),(4,6,'available'),(5,6,'available'),
(6,6,'available'),(7,6,'available'),(8,6,'available'),(9,6,'available'),(10,6,'available'),
(11,6,'available'),(12,6,'available'),(13,6,'available'),(14,6,'available'),(15,6,'available'),
(16,6,'available'),(17,6,'available'),(18,6,'available'),(19,6,'available'),(20,6,'available'),
(21,6,'available'),(22,6,'available'),(23,6,'available'),(24,6,'available'),(25,6,'available'),
(26,6,'available'),(27,6,'available'),(28,6,'available'),(29,6,'available'),(30,6,'available'),
(31,6,'available'),(32,6,'available'),(33,6,'available'),(34,6,'available'),(35,6,'available'),
(36,6,'available'),(37,6,'available'),(38,6,'available'),(39,6,'available'),(40,6,'available'),
-- schedule 7
(1,7,'available'),(2,7,'available'),(3,7,'available'),(4,7,'available'),(5,7,'available'),
(6,7,'available'),(7,7,'available'),(8,7,'available'),(9,7,'available'),(10,7,'available'),
(11,7,'available'),(12,7,'available'),(13,7,'available'),(14,7,'available'),(15,7,'available'),
(16,7,'available'),(17,7,'available'),(18,7,'available'),(19,7,'available'),(20,7,'available'),
(21,7,'available'),(22,7,'available'),(23,7,'available'),(24,7,'available'),(25,7,'available'),
(26,7,'available'),(27,7,'available'),(28,7,'available'),(29,7,'available'),(30,7,'available'),
(31,7,'available'),(32,7,'available'),(33,7,'available'),(34,7,'available'),(35,7,'available'),
(36,7,'available'),(37,7,'available'),(38,7,'available'),(39,7,'available'),(40,7,'available');

-- Bus 2 seats (seat_id 41-85) × schedules 8-14
INSERT INTO seat_availability (seat_id, schedule_id, status) VALUES
-- schedule 8
(41,8,'available'),(42,8,'available'),(43,8,'available'),(44,8,'available'),(45,8,'available'),
(46,8,'available'),(47,8,'available'),(48,8,'available'),(49,8,'available'),(50,8,'available'),
(51,8,'available'),(52,8,'available'),(53,8,'available'),(54,8,'available'),(55,8,'available'),
(56,8,'available'),(57,8,'available'),(58,8,'available'),(59,8,'available'),(60,8,'available'),
(61,8,'available'),(62,8,'available'),(63,8,'available'),(64,8,'available'),(65,8,'available'),
(66,8,'available'),(67,8,'available'),(68,8,'available'),(69,8,'available'),(70,8,'available'),
(71,8,'available'),(72,8,'available'),(73,8,'available'),(74,8,'available'),(75,8,'available'),
(76,8,'available'),(77,8,'available'),(78,8,'available'),(79,8,'available'),(80,8,'available'),
(81,8,'available'),(82,8,'available'),(83,8,'available'),(84,8,'available'),(85,8,'available'),
-- schedule 9
(41,9,'available'),(42,9,'available'),(43,9,'available'),(44,9,'available'),(45,9,'available'),
(46,9,'available'),(47,9,'available'),(48,9,'available'),(49,9,'available'),(50,9,'available'),
(51,9,'available'),(52,9,'available'),(53,9,'available'),(54,9,'available'),(55,9,'available'),
(56,9,'available'),(57,9,'available'),(58,9,'available'),(59,9,'available'),(60,9,'available'),
(61,9,'available'),(62,9,'available'),(63,9,'available'),(64,9,'available'),(65,9,'available'),
(66,9,'available'),(67,9,'available'),(68,9,'available'),(69,9,'available'),(70,9,'available'),
(71,9,'available'),(72,9,'available'),(73,9,'available'),(74,9,'available'),(75,9,'available'),
(76,9,'available'),(77,9,'available'),(78,9,'available'),(79,9,'available'),(80,9,'available'),
(81,9,'available'),(82,9,'available'),(83,9,'available'),(84,9,'available'),(85,9,'available'),
-- schedule 10
(41,10,'available'),(42,10,'available'),(43,10,'available'),(44,10,'available'),(45,10,'available'),
(46,10,'available'),(47,10,'available'),(48,10,'available'),(49,10,'available'),(50,10,'available'),
(51,10,'available'),(52,10,'available'),(53,10,'available'),(54,10,'available'),(55,10,'available'),
(56,10,'available'),(57,10,'available'),(58,10,'available'),(59,10,'available'),(60,10,'available'),
(61,10,'available'),(62,10,'available'),(63,10,'available'),(64,10,'available'),(65,10,'available'),
(66,10,'available'),(67,10,'available'),(68,10,'available'),(69,10,'available'),(70,10,'available'),
(71,10,'available'),(72,10,'available'),(73,10,'available'),(74,10,'available'),(75,10,'available'),
(76,10,'available'),(77,10,'available'),(78,10,'available'),(79,10,'available'),(80,10,'available'),
(81,10,'available'),(82,10,'available'),(83,10,'available'),(84,10,'available'),(85,10,'available'),
-- schedule 11
(41,11,'available'),(42,11,'available'),(43,11,'available'),(44,11,'available'),(45,11,'available'),
(46,11,'available'),(47,11,'available'),(48,11,'available'),(49,11,'available'),(50,11,'available'),
(51,11,'available'),(52,11,'available'),(53,11,'available'),(54,11,'available'),(55,11,'available'),
(56,11,'available'),(57,11,'available'),(58,11,'available'),(59,11,'available'),(60,11,'available'),
(61,11,'available'),(62,11,'available'),(63,11,'available'),(64,11,'available'),(65,11,'available'),
(66,11,'available'),(67,11,'available'),(68,11,'available'),(69,11,'available'),(70,11,'available'),
(71,11,'available'),(72,11,'available'),(73,11,'available'),(74,11,'available'),(75,11,'available'),
(76,11,'available'),(77,11,'available'),(78,11,'available'),(79,11,'available'),(80,11,'available'),
(81,11,'available'),(82,11,'available'),(83,11,'available'),(84,11,'available'),(85,11,'available'),
-- schedule 12
(41,12,'available'),(42,12,'available'),(43,12,'available'),(44,12,'available'),(45,12,'available'),
(46,12,'available'),(47,12,'available'),(48,12,'available'),(49,12,'available'),(50,12,'available'),
(51,12,'available'),(52,12,'available'),(53,12,'available'),(54,12,'available'),(55,12,'available'),
(56,12,'available'),(57,12,'available'),(58,12,'available'),(59,12,'available'),(60,12,'available'),
(61,12,'available'),(62,12,'available'),(63,12,'available'),(64,12,'available'),(65,12,'available'),
(66,12,'available'),(67,12,'available'),(68,12,'available'),(69,12,'available'),(70,12,'available'),
(71,12,'available'),(72,12,'available'),(73,12,'available'),(74,12,'available'),(75,12,'available'),
(76,12,'available'),(77,12,'available'),(78,12,'available'),(79,12,'available'),(80,12,'available'),
(81,12,'available'),(82,12,'available'),(83,12,'available'),(84,12,'available'),(85,12,'available'),
-- schedule 13
(41,13,'available'),(42,13,'available'),(43,13,'available'),(44,13,'available'),(45,13,'available'),
(46,13,'available'),(47,13,'available'),(48,13,'available'),(49,13,'available'),(50,13,'available'),
(51,13,'available'),(52,13,'available'),(53,13,'available'),(54,13,'available'),(55,13,'available'),
(56,13,'available'),(57,13,'available'),(58,13,'available'),(59,13,'available'),(60,13,'available'),
(61,13,'available'),(62,13,'available'),(63,13,'available'),(64,13,'available'),(65,13,'available'),
(66,13,'available'),(67,13,'available'),(68,13,'available'),(69,13,'available'),(70,13,'available'),
(71,13,'available'),(72,13,'available'),(73,13,'available'),(74,13,'available'),(75,13,'available'),
(76,13,'available'),(77,13,'available'),(78,13,'available'),(79,13,'available'),(80,13,'available'),
(81,13,'available'),(82,13,'available'),(83,13,'available'),(84,13,'available'),(85,13,'available'),
-- schedule 14
(41,14,'available'),(42,14,'available'),(43,14,'available'),(44,14,'available'),(45,14,'available'),
(46,14,'available'),(47,14,'available'),(48,14,'available'),(49,14,'available'),(50,14,'available'),
(51,14,'available'),(52,14,'available'),(53,14,'available'),(54,14,'available'),(55,14,'available'),
(56,14,'available'),(57,14,'available'),(58,14,'available'),(59,14,'available'),(60,14,'available'),
(61,14,'available'),(62,14,'available'),(63,14,'available'),(64,14,'available'),(65,14,'available'),
(66,14,'available'),(67,14,'available'),(68,14,'available'),(69,14,'available'),(70,14,'available'),
(71,14,'available'),(72,14,'available'),(73,14,'available'),(74,14,'available'),(75,14,'available'),
(76,14,'available'),(77,14,'available'),(78,14,'available'),(79,14,'available'),(80,14,'available'),
(81,14,'available'),(82,14,'available'),(83,14,'available'),(84,14,'available'),(85,14,'available');

-- ============================================================
-- COUPONS
-- ============================================================
INSERT INTO coupons (code, discount_type, discount_value, min_booking_amount, max_discount, valid_from, valid_until, usage_limit, is_active) VALUES
('FIRST10', 'percentage', 10.00, 0.00,   200.00, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 1 YEAR), 1000, 1),
('SAVE100', 'fixed',     100.00, 500.00,   NULL,  CURDATE(), DATE_ADD(CURDATE(), INTERVAL 1 YEAR),  500, 1);

-- ============================================================
-- END OF SEED DATA
-- ============================================================
