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
-- 6. Индексы
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_machines_workshop_id
    ON equipment.machines(workshop_id);

CREATE INDEX IF NOT EXISTS idx_machines_inventory_number
    ON equipment.machines(inventory_number);

CREATE INDEX IF NOT EXISTS idx_machines_machine_name
    ON equipment.machines(machine_name);

CREATE INDEX IF NOT EXISTS idx_machine_maintenance_machine_id
    ON equipment.machine_maintenance(machine_id);
