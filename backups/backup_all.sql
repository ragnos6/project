--
-- PostgreSQL database cluster dump
--

SET default_transaction_read_only = off;

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

--
-- Roles
--

CREATE ROLE hunter;
ALTER ROLE hunter WITH SUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS PASSWORD 'SCRAM-SHA-256$4096:FiZ4zDyQNvX4G5y+XccYaw==$Kn2L9QLuvZ5HaeaTUZ7SVbgimOaprtvYu65sj8OKUpw=:PNhneg6JTobdR2ofL0wnKfYLvzrw6RDGQRuN8187RRo=';
CREATE ROLE postgres;
ALTER ROLE postgres WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS PASSWORD 'SCRAM-SHA-256$4096:JCyhivmdQ+ECuwdzID9lJA==$AnQiCX5VM1krsjpjwjdKnlAhrukyjAdcd2anwWp0QGg=:GUPsYCPywNs6USdZofgn624gXxIdCoPkzs55yzGTF4M=';






--
-- Databases
--

--
-- Database "template1" dump
--

\connect template1

