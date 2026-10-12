CREATE TABLE IF NOT EXISTS addresses (
    state CHAR(2) NOT NULL,
    city VARCHAR(75) NOT NULL,
    neighborhood VARCHAR(100),
    zipcode CHAR(8) NOT NULL,
    street VARCHAR(150),
    PRIMARY KEY (zipcode),
    INDEX idx_city (city)
)ENGINE=InnoDB;
