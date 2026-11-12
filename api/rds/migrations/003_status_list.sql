-- Each credential gets a fixed position in the issuer's public W3C Bitstring Status List (revocation purpose).
ALTER TABLE credentials ADD COLUMN status_index INTEGER;
CREATE UNIQUE INDEX credentials_status_index ON credentials (status_index);
