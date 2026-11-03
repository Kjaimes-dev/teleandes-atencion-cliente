-- Esquema de TeleAndes. Se ejecuta solo en el primer arranque del contenedor.
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS clientes (
    documento    VARCHAR(10)  NOT NULL,
    nombre       VARCHAR(120) NOT NULL,
    celular      VARCHAR(15)  NOT NULL,
    plan         VARCHAR(80)  NOT NULL,
    estado       ENUM('activo', 'suspendido') NOT NULL,
    saldo        INT          NOT NULL DEFAULT 0 COMMENT 'Pesos colombianos, sin decimales',
    fecha_corte  DATE         NOT NULL,
    PRIMARY KEY (documento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS gestiones (
    id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    -- NULL solo en gestiones de ivr y whatsapp sin cliente identificado; la FK
    -- se aplica cuando hay valor (MySQL admite NULL en una clave foránea).
    documento        VARCHAR(10)   NULL,
    canal            ENUM('ivr', 'whatsapp', 'agente') NOT NULL,
    tipificacion     VARCHAR(30)   NOT NULL,
    observacion      VARCHAR(1000) NOT NULL DEFAULT '',
    -- Hora local de America/Bogota (UTC-5, sin horario de verano).
    fecha            DATETIME(3)   NOT NULL,
    idempotency_key  VARCHAR(64)   NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_gestiones_idempotency_key (idempotency_key),
    KEY idx_gestiones_documento_fecha (documento, fecha),
    KEY idx_gestiones_fecha (fecha),
    CONSTRAINT fk_gestiones_cliente FOREIGN KEY (documento)
        REFERENCES clientes (documento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
