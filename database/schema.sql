-- ============================================================
-- DATABASE SCHEMA: Equipment
-- ============================================================

-- ------------------------------------------------------------
-- 1. Создание схемы
-- ------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS equipment;


-- ============================================================
-- 2. Таблица цехов
-- ============================================================

CREATE TABLE IF NOT EXISTS equipment.workshops (
    id BIGSERIAL PRIMARY KEY,

    name VARCHAR(100) NOT NULL,

    description TEXT
);


-- ============================================================
-- 3. Таблица станков
-- ============================================================

CREATE TABLE IF NOT EXISTS equipment.machines (
    id BIGSERIAL PRIMARY KEY,

    workshop_id BIGINT NOT NULL,

    inventory_number INTEGER,

    machine_name VARCHAR(200) NOT NULL,

    folder_path TEXT,

    controller VARCHAR(200),

    status VARCHAR(50) NOT NULL DEFAULT 'В работе',

    commissioning_year INTEGER,

    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_machines_workshop
        FOREIGN KEY (workshop_id)
        REFERENCES equipment.workshops(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


-- ============================================================
-- 4. Характеристики компьютера станка
-- ============================================================

CREATE TABLE IF NOT EXISTS equipment.computer_specs (
    id BIGSERIAL PRIMARY KEY,

    machine_id BIGINT NOT NULL,

    mac_address VARCHAR(17),

    ip_address VARCHAR(45),

    screen VARCHAR(255),

    processor VARCHAR(255),

    ram VARCHAR(100),

    rom VARCHAR(100),

    operating_system VARCHAR(200),

    antivirus VARCHAR(255),

    CONSTRAINT uq_computer_specs_machine
        UNIQUE (machine_id),

    CONSTRAINT fk_computer_specs_machine
        FOREIGN KEY (machine_id)
        REFERENCES equipment.machines(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- ============================================================
-- 5. История обслуживания и неисправностей
-- ============================================================

CREATE TABLE IF NOT EXISTS equipment.machine_maintenance (
    id BIGSERIAL PRIMARY KEY,

    machine_id BIGINT NOT NULL,

    work_type VARCHAR(200),

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    start_date TIMESTAMP WITH TIME ZONE,

    end_date TIMESTAMP WITHOUT TIME ZONE,

    work_performed TEXT,

    notes TEXT,

    CONSTRAINT fk_machine_maintenance_machine
        FOREIGN KEY (machine_id)
        REFERENCES equipment.machines(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- ============================================================
-- 6. Индексы и расширения для высокой скорости поиска
-- ============================================================

-- Включаем модуль триграмм для быстрого поиска ILIKE по подстрокам
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_machines_workshop_id
    ON equipment.machines(workshop_id);

CREATE INDEX IF NOT EXISTS idx_machines_inventory_number
    ON equipment.machines(inventory_number);

CREATE INDEX IF NOT EXISTS idx_machines_machine_name
    ON equipment.machines(machine_name);

-- GIN триграммные индексы для мгновенного поиска по подстроке (ILIKE '%...%')
CREATE INDEX IF NOT EXISTS idx_machines_machine_name_trgm
    ON equipment.machines USING gin (machine_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_machines_controller_trgm
    ON equipment.machines USING gin (controller gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_machines_inventory_number_trgm
    ON equipment.machines USING gin ((inventory_number::text) gin_trgm_ops);

-- Составной индекс для быстрой выборки истории обслуживания оборудования
CREATE INDEX IF NOT EXISTS idx_machine_maintenance_machine_date
    ON equipment.machine_maintenance (machine_id, start_date DESC NULLS LAST, id DESC);


-- ============================================================
-- 7. Представления (Views) для оптимизации запросов
-- ============================================================

CREATE OR REPLACE VIEW equipment.v_machines_full AS
SELECT
    m.id,
    m.inventory_number,
    m.machine_name,
    m.machine_name AS name,
    m.workshop_id,
    w.name AS workshop_name,
    w.description AS workshop_description,
    m.folder_path,
    m.folder_path AS sub_folder,
    m.controller,
    m.status,
    m.commissioning_year,
    m.commissioning_year AS year_built,
    cs.ip_address,
    cs.mac_address,
    cs.screen,
    cs.processor,
    cs.ram,
    cs.rom,
    cs.operating_system,
    cs.antivirus,
    m.created_at,
    m.updated_at
FROM equipment.machines m
LEFT JOIN equipment.workshops w ON w.id = m.workshop_id
LEFT JOIN equipment.computer_specs cs ON cs.machine_id = m.id;


-- ============================================================
-- 8. Таблица пользователей и прав доступа
-- ============================================================

CREATE TABLE IF NOT EXISTS equipment.users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150),
    role VARCHAR(20) NOT NULL DEFAULT 'viewer', -- 'admin', 'editor', 'viewer'
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON equipment.users(username);


