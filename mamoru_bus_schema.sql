--
-- PostgreSQL database dump
--

\restrict pUzcEesldkCiN2bDOp1DTt9ZA8ZdQVkWhz4wbNDEdg0Re3xe9tFP2bdcye8aKP8

-- Dumped from database version 18.4 (Debian 18.4-1.pgdg12+1)
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: pg_stat_statements; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_stat_statements WITH SCHEMA public;


--
-- Name: EXTENSION pg_stat_statements; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_stat_statements IS 'track planning and execution statistics of all SQL statements executed';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: admin_pin_recoveries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.admin_pin_recoveries (
    token_hash character varying(64) NOT NULL,
    staff_id integer NOT NULL,
    used_at timestamp without time zone NOT NULL
);


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    actor_id integer,
    action character varying(100) NOT NULL,
    resource_type character varying(60) NOT NULL,
    resource_id character varying(60) NOT NULL,
    detail text NOT NULL,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: bus_routes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bus_routes (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    direction character varying(20) NOT NULL,
    vehicle_id integer,
    organization_id integer,
    is_active boolean DEFAULT true
);


--
-- Name: bus_routes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bus_routes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bus_routes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bus_routes_id_seq OWNED BY public.bus_routes.id;


--
-- Name: bus_trips; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bus_trips (
    id integer NOT NULL,
    route_id integer,
    vehicle_id integer,
    direction character varying(20) NOT NULL,
    status character varying(30) NOT NULL,
    started_at timestamp without time zone NOT NULL,
    completed_at timestamp without time zone,
    organization_id integer
);


--
-- Name: bus_trips_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bus_trips_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bus_trips_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bus_trips_id_seq OWNED BY public.bus_trips.id;


--
-- Name: child_guardians; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.child_guardians (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    child_id integer NOT NULL,
    guardian_contact_id integer NOT NULL,
    relationship character varying(50),
    notify_alighted boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: child_guardians_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.child_guardians_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: child_guardians_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.child_guardians_id_seq OWNED BY public.child_guardians.id;


--
-- Name: children; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.children (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    class_name character varying(50),
    qr_token character varying(100) NOT NULL,
    organization_id integer
);


--
-- Name: children_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.children_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: children_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.children_id_seq OWNED BY public.children.id;


--
-- Name: guardian_contacts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.guardian_contacts (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    name character varying(100),
    email character varying(254) NOT NULL,
    email_normalized character varying(254) NOT NULL,
    email_enabled boolean NOT NULL,
    line_enabled boolean NOT NULL,
    line_status character varying(30) NOT NULL,
    consented_at timestamp without time zone,
    consented_by integer,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: guardian_contacts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.guardian_contacts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: guardian_contacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.guardian_contacts_id_seq OWNED BY public.guardian_contacts.id;


--
-- Name: line_contacts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.line_contacts (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    line_user_id character varying(100) NOT NULL,
    display_name character varying(100),
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    guardian_contact_id integer,
    last_webhook_event_id character varying(160),
    last_event_at timestamp without time zone
);


--
-- Name: line_contacts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.line_contacts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: line_contacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.line_contacts_id_seq OWNED BY public.line_contacts.id;


--
-- Name: line_link_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.line_link_requests (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    guardian_contact_id integer NOT NULL,
    token_hash character varying(64) NOT NULL,
    status character varying(20) NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    requested_by integer NOT NULL,
    email_notification_id integer,
    used_at timestamp without time zone,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: line_link_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.line_link_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: line_link_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.line_link_requests_id_seq OWNED BY public.line_link_requests.id;


--
-- Name: notification_queue; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notification_queue (
    id integer NOT NULL,
    recipient_type character varying(30) NOT NULL,
    recipient character varying(200) NOT NULL,
    message character varying(500) NOT NULL,
    status character varying(30) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    organization_id integer,
    channel character varying(30) DEFAULT 'webhook'::character varying,
    provider_response text,
    sent_at timestamp without time zone,
    guardian_contact_id integer,
    child_id integer,
    event_key character varying(160),
    template_key character varying(60),
    subject character varying(200),
    attempt_count integer DEFAULT 0,
    next_attempt_at timestamp without time zone,
    provider_message_id character varying(200),
    error_code character varying(60)
);


--
-- Name: notification_queue_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.notification_queue_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: notification_queue_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.notification_queue_id_seq OWNED BY public.notification_queue.id;


--
-- Name: organizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organizations (
    id integer NOT NULL,
    name character varying(120) NOT NULL,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: organizations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.organizations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: organizations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.organizations_id_seq OWNED BY public.organizations.id;


--
-- Name: route_children; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.route_children (
    id integer NOT NULL,
    route_id integer NOT NULL,
    child_id integer NOT NULL
);


--
-- Name: route_children_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.route_children_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: route_children_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.route_children_id_seq OWNED BY public.route_children.id;


--
-- Name: safety_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.safety_events (
    id integer NOT NULL,
    child_id integer,
    event_type character varying(40) NOT NULL,
    staff_name character varying(100) NOT NULL,
    latitude character varying(30),
    longitude character varying(30),
    created_at timestamp without time zone NOT NULL
);


--
-- Name: safety_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.safety_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: safety_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.safety_events_id_seq OWNED BY public.safety_events.id;


--
-- Name: staff; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.staff (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    role character varying(40) NOT NULL,
    pin_hash character varying(64) NOT NULL,
    organization_id integer,
    password_hash character varying(256),
    is_active boolean DEFAULT true
);


--
-- Name: staff_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.staff_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: staff_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.staff_id_seq OWNED BY public.staff.id;


--
-- Name: sync_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sync_events (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    client_event_id character varying(80) NOT NULL,
    outcome character varying(30) NOT NULL,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: sync_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sync_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sync_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sync_events_id_seq OWNED BY public.sync_events.id;


--
-- Name: trip_attendance; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trip_attendance (
    id integer NOT NULL,
    trip_id integer NOT NULL,
    child_id integer NOT NULL,
    boarded_at timestamp without time zone,
    alighted_at timestamp without time zone,
    boarded_by character varying(100),
    alighted_by character varying(100)
);


--
-- Name: trip_attendance_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.trip_attendance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: trip_attendance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.trip_attendance_id_seq OWNED BY public.trip_attendance.id;


--
-- Name: vehicle_safety_checks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vehicle_safety_checks (
    id integer NOT NULL,
    check_type character varying(40) NOT NULL,
    staff_id integer NOT NULL,
    staff_name character varying(100) NOT NULL,
    qr_token character varying(100) NOT NULL,
    latitude character varying(30),
    longitude character varying(30),
    created_at timestamp without time zone NOT NULL,
    organization_id integer,
    trip_id integer
);


--
-- Name: vehicle_safety_checks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vehicle_safety_checks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: vehicle_safety_checks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vehicle_safety_checks_id_seq OWNED BY public.vehicle_safety_checks.id;


--
-- Name: vehicles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vehicles (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    plate_number character varying(30),
    organization_id integer,
    is_active boolean DEFAULT true
);


--
-- Name: vehicles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vehicles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: vehicles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vehicles_id_seq OWNED BY public.vehicles.id;


--
-- Name: video_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.video_evidence (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    trip_id integer NOT NULL,
    uploaded_by integer NOT NULL,
    file_name character varying(255) NOT NULL,
    storage_key character varying(255) NOT NULL,
    content_type character varying(100) NOT NULL,
    ai_status character varying(30) NOT NULL,
    ai_result text,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: video_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.video_evidence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: video_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.video_evidence_id_seq OWNED BY public.video_evidence.id;


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: bus_routes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bus_routes ALTER COLUMN id SET DEFAULT nextval('public.bus_routes_id_seq'::regclass);


--
-- Name: bus_trips id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bus_trips ALTER COLUMN id SET DEFAULT nextval('public.bus_trips_id_seq'::regclass);


--
-- Name: child_guardians id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.child_guardians ALTER COLUMN id SET DEFAULT nextval('public.child_guardians_id_seq'::regclass);


--
-- Name: children id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.children ALTER COLUMN id SET DEFAULT nextval('public.children_id_seq'::regclass);


--
-- Name: guardian_contacts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guardian_contacts ALTER COLUMN id SET DEFAULT nextval('public.guardian_contacts_id_seq'::regclass);


--
-- Name: line_contacts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.line_contacts ALTER COLUMN id SET DEFAULT nextval('public.line_contacts_id_seq'::regclass);


--
-- Name: line_link_requests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.line_link_requests ALTER COLUMN id SET DEFAULT nextval('public.line_link_requests_id_seq'::regclass);


--
-- Name: notification_queue id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_queue ALTER COLUMN id SET DEFAULT nextval('public.notification_queue_id_seq'::regclass);


--
-- Name: organizations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations ALTER COLUMN id SET DEFAULT nextval('public.organizations_id_seq'::regclass);


--
-- Name: route_children id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_children ALTER COLUMN id SET DEFAULT nextval('public.route_children_id_seq'::regclass);


--
-- Name: safety_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.safety_events ALTER COLUMN id SET DEFAULT nextval('public.safety_events_id_seq'::regclass);


--
-- Name: staff id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff ALTER COLUMN id SET DEFAULT nextval('public.staff_id_seq'::regclass);


--
-- Name: sync_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_events ALTER COLUMN id SET DEFAULT nextval('public.sync_events_id_seq'::regclass);


--
-- Name: trip_attendance id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_attendance ALTER COLUMN id SET DEFAULT nextval('public.trip_attendance_id_seq'::regclass);


--
-- Name: vehicle_safety_checks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehicle_safety_checks ALTER COLUMN id SET DEFAULT nextval('public.vehicle_safety_checks_id_seq'::regclass);


--
-- Name: vehicles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehicles ALTER COLUMN id SET DEFAULT nextval('public.vehicles_id_seq'::regclass);


--
-- Name: video_evidence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_evidence ALTER COLUMN id SET DEFAULT nextval('public.video_evidence_id_seq'::regclass);


--
-- Name: admin_pin_recoveries admin_pin_recoveries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.admin_pin_recoveries
    ADD CONSTRAINT admin_pin_recoveries_pkey PRIMARY KEY (token_hash);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: bus_routes bus_routes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bus_routes
    ADD CONSTRAINT bus_routes_pkey PRIMARY KEY (id);


--
-- Name: bus_trips bus_trips_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bus_trips
    ADD CONSTRAINT bus_trips_pkey PRIMARY KEY (id);


--
-- Name: child_guardians child_guardians_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.child_guardians
    ADD CONSTRAINT child_guardians_pkey PRIMARY KEY (id);


--
-- Name: children children_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.children
    ADD CONSTRAINT children_pkey PRIMARY KEY (id);


--
-- Name: children children_qr_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.children
    ADD CONSTRAINT children_qr_token_key UNIQUE (qr_token);


--
-- Name: guardian_contacts guardian_contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guardian_contacts
    ADD CONSTRAINT guardian_contacts_pkey PRIMARY KEY (id);


--
-- Name: line_contacts line_contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.line_contacts
    ADD CONSTRAINT line_contacts_pkey PRIMARY KEY (id);


--
-- Name: line_link_requests line_link_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.line_link_requests
    ADD CONSTRAINT line_link_requests_pkey PRIMARY KEY (id);


--
-- Name: line_link_requests line_link_requests_token_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.line_link_requests
    ADD CONSTRAINT line_link_requests_token_hash_key UNIQUE (token_hash);


--
-- Name: notification_queue notification_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_queue
    ADD CONSTRAINT notification_queue_pkey PRIMARY KEY (id);


--
-- Name: organizations organizations_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_name_key UNIQUE (name);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- Name: route_children route_children_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_children
    ADD CONSTRAINT route_children_pkey PRIMARY KEY (id);


--
-- Name: safety_events safety_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.safety_events
    ADD CONSTRAINT safety_events_pkey PRIMARY KEY (id);


--
-- Name: staff staff_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_pkey PRIMARY KEY (id);


--
-- Name: sync_events sync_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_events
    ADD CONSTRAINT sync_events_pkey PRIMARY KEY (id);


--
-- Name: trip_attendance trip_attendance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_attendance
    ADD CONSTRAINT trip_attendance_pkey PRIMARY KEY (id);


--
-- Name: child_guardians uq_child_guardian; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.child_guardians
    ADD CONSTRAINT uq_child_guardian UNIQUE (organization_id, child_id, guardian_contact_id);


--
-- Name: guardian_contacts uq_guardian_contact_org_email; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guardian_contacts
    ADD CONSTRAINT uq_guardian_contact_org_email UNIQUE (organization_id, email_normalized);


--
-- Name: line_contacts uq_line_contact_org_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.line_contacts
    ADD CONSTRAINT uq_line_contact_org_user UNIQUE (organization_id, line_user_id);


--
-- Name: route_children uq_route_child; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_children
    ADD CONSTRAINT uq_route_child UNIQUE (route_id, child_id);


--
-- Name: sync_events uq_sync_org_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_events
    ADD CONSTRAINT uq_sync_org_event UNIQUE (organization_id, client_event_id);


--
-- Name: vehicle_safety_checks vehicle_safety_checks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehicle_safety_checks
    ADD CONSTRAINT vehicle_safety_checks_pkey PRIMARY KEY (id);


--
-- Name: vehicles vehicles_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_name_key UNIQUE (name);


--
-- Name: vehicles vehicles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_pkey PRIMARY KEY (id);


--
-- Name: video_evidence video_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_evidence
    ADD CONSTRAINT video_evidence_pkey PRIMARY KEY (id);


--
-- Name: video_evidence video_evidence_storage_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_evidence
    ADD CONSTRAINT video_evidence_storage_key_key UNIQUE (storage_key);


--
-- Name: ix_audit_logs_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: ix_audit_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_created_at ON public.audit_logs USING btree (created_at);


--
-- Name: ix_audit_logs_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_organization_id ON public.audit_logs USING btree (organization_id);


--
-- Name: ix_child_guardians_child_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_child_guardians_child_id ON public.child_guardians USING btree (child_id);


--
-- Name: ix_child_guardians_guardian_contact_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_child_guardians_guardian_contact_id ON public.child_guardians USING btree (guardian_contact_id);


--
-- Name: ix_child_guardians_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_child_guardians_organization_id ON public.child_guardians USING btree (organization_id);


--
-- Name: ix_guardian_contacts_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_guardian_contacts_organization_id ON public.guardian_contacts USING btree (organization_id);


--
-- Name: ix_line_contacts_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_line_contacts_organization_id ON public.line_contacts USING btree (organization_id);


--
-- Name: ix_line_link_requests_guardian_contact_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_line_link_requests_guardian_contact_id ON public.line_link_requests USING btree (guardian_contact_id);


--
-- Name: ix_line_link_requests_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_line_link_requests_organization_id ON public.line_link_requests USING btree (organization_id);


--
-- Name: ix_line_link_requests_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_line_link_requests_status ON public.line_link_requests USING btree (status);


--
-- Name: ix_route_children_child_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_route_children_child_id ON public.route_children USING btree (child_id);


--
-- Name: ix_route_children_route_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_route_children_route_id ON public.route_children USING btree (route_id);


--
-- Name: ix_sync_events_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sync_events_organization_id ON public.sync_events USING btree (organization_id);


--
-- Name: ix_video_evidence_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_evidence_organization_id ON public.video_evidence USING btree (organization_id);


--
-- Name: admin_pin_recoveries admin_pin_recoveries_staff_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.admin_pin_recoveries
    ADD CONSTRAINT admin_pin_recoveries_staff_id_fkey FOREIGN KEY (staff_id) REFERENCES public.staff(id);


--
-- Name: audit_logs audit_logs_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES public.staff(id);


--
-- Name: audit_logs audit_logs_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: bus_routes bus_routes_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bus_routes
    ADD CONSTRAINT bus_routes_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id);


--
-- Name: bus_trips bus_trips_route_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bus_trips
    ADD CONSTRAINT bus_trips_route_id_fkey FOREIGN KEY (route_id) REFERENCES public.bus_routes(id);


--
-- Name: bus_trips bus_trips_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bus_trips
    ADD CONSTRAINT bus_trips_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id);


--
-- Name: child_guardians child_guardians_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.child_guardians
    ADD CONSTRAINT child_guardians_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.children(id);


--
-- Name: child_guardians child_guardians_guardian_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.child_guardians
    ADD CONSTRAINT child_guardians_guardian_contact_id_fkey FOREIGN KEY (guardian_contact_id) REFERENCES public.guardian_contacts(id);


--
-- Name: child_guardians child_guardians_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.child_guardians
    ADD CONSTRAINT child_guardians_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: guardian_contacts guardian_contacts_consented_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guardian_contacts
    ADD CONSTRAINT guardian_contacts_consented_by_fkey FOREIGN KEY (consented_by) REFERENCES public.staff(id);


--
-- Name: guardian_contacts guardian_contacts_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guardian_contacts
    ADD CONSTRAINT guardian_contacts_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: line_contacts line_contacts_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.line_contacts
    ADD CONSTRAINT line_contacts_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: line_link_requests line_link_requests_email_notification_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.line_link_requests
    ADD CONSTRAINT line_link_requests_email_notification_id_fkey FOREIGN KEY (email_notification_id) REFERENCES public.notification_queue(id);


--
-- Name: line_link_requests line_link_requests_guardian_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.line_link_requests
    ADD CONSTRAINT line_link_requests_guardian_contact_id_fkey FOREIGN KEY (guardian_contact_id) REFERENCES public.guardian_contacts(id);


--
-- Name: line_link_requests line_link_requests_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.line_link_requests
    ADD CONSTRAINT line_link_requests_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: line_link_requests line_link_requests_requested_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.line_link_requests
    ADD CONSTRAINT line_link_requests_requested_by_fkey FOREIGN KEY (requested_by) REFERENCES public.staff(id);


--
-- Name: route_children route_children_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_children
    ADD CONSTRAINT route_children_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.children(id);


--
-- Name: route_children route_children_route_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_children
    ADD CONSTRAINT route_children_route_id_fkey FOREIGN KEY (route_id) REFERENCES public.bus_routes(id);


--
-- Name: safety_events safety_events_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.safety_events
    ADD CONSTRAINT safety_events_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.children(id);


--
-- Name: sync_events sync_events_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_events
    ADD CONSTRAINT sync_events_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: trip_attendance trip_attendance_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_attendance
    ADD CONSTRAINT trip_attendance_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.children(id);


--
-- Name: trip_attendance trip_attendance_trip_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_attendance
    ADD CONSTRAINT trip_attendance_trip_id_fkey FOREIGN KEY (trip_id) REFERENCES public.bus_trips(id);


--
-- Name: vehicle_safety_checks vehicle_safety_checks_staff_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehicle_safety_checks
    ADD CONSTRAINT vehicle_safety_checks_staff_id_fkey FOREIGN KEY (staff_id) REFERENCES public.staff(id);


--
-- Name: video_evidence video_evidence_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_evidence
    ADD CONSTRAINT video_evidence_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: video_evidence video_evidence_trip_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_evidence
    ADD CONSTRAINT video_evidence_trip_id_fkey FOREIGN KEY (trip_id) REFERENCES public.bus_trips(id);


--
-- Name: video_evidence video_evidence_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_evidence
    ADD CONSTRAINT video_evidence_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.staff(id);


--
-- PostgreSQL database dump complete
--

\unrestrict pUzcEesldkCiN2bDOp1DTt9ZA8ZdQVkWhz4wbNDEdg0Re3xe9tFP2bdcye8aKP8

