-- Deletes all tables and data in EvacBridge.
-- Run the schema and seed scripts after this reset completes.

DROP DATABASE IF EXISTS `EvacBridge`;
CREATE DATABASE `EvacBridge`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE `EvacBridge`;
