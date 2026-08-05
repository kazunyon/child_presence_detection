--
-- PostgreSQL database dump
--

\restrict PT4bwAZNNX18ltxXCNSMwikdxQM9pe96EhCgtZtbAF7ydlsG7RNq4a79gHaj621

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
-- Data for Name: staff; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.staff (id, name, role, pin_hash, organization_id, password_hash, is_active) FROM stdin;
1	田中 先生	operator	03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4	8	pbkdf2_sha256$210000$1XuLmzZAm+xlTQCe9WCRLHuQCFksyZ2AyEFJJZ0v1EHE6ebz8pY7KZz9VeYi44h3	t
2	佐藤 先生	verifier	f8638b979b2f4f793ddb6dbd197e0ee25a7a6ea32b0ae22f5e3c5d119d839e75	8	pbkdf2_sha256$210000$AKUqxuvTJC92gq5UJqG/cwS/stiEHZsU7P1pHnXEj6Q00uv3J8Ttu9UFTG+buCwe	t
3	管理者	admin	6ed79eeac110f54d0cbfbcea581d7953547b6e17f953c4a6fcf1365e8f2ad910	8	pbkdf2_sha256$210000$2q3XOZyMI/37wCiNzgZJaY2EBRDNCwAti77wXRePhJoS6iNnTnNcKObeQHr6C799	t
\.


--
-- Data for Name: admin_pin_recoveries; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.admin_pin_recoveries (token_hash, staff_id, used_at) FROM stdin;
914ed58e5d6e2f4035127bf77d52e34aadf8975f10cea4389ceaa3a55ac9a022	3	2026-07-24 04:51:08.136673
\.


--
-- Data for Name: organizations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.organizations (id, name, created_at) FROM stdin;
8	植竹幼稚園	2026-07-23 23:22:30.133704
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.audit_logs (id, organization_id, actor_id, action, resource_type, resource_id, detail, created_at) FROM stdin;
1	8	1	auth.login	staff	1	{}	2026-07-23 23:23:06.790591
2	8	1	auth.login	staff	1	{}	2026-07-23 23:27:37.180814
3	8	1	auth.login	staff	1	{}	2026-07-23 23:28:05.690335
4	8	1	auth.login	staff	1	{}	2026-07-23 23:30:25.879155
5	8	1	auth.login	staff	1	{}	2026-07-23 23:31:24.526929
6	8	1	auth.login	staff	1	{}	2026-07-23 23:31:53.740056
7	8	1	trip.create	trip	4	{}	2026-07-23 23:38:15.130091
8	8	1	auth.login	staff	1	{}	2026-07-23 23:41:26.919464
9	8	1	auth.login	staff	1	{}	2026-07-23 23:44:26.019922
10	8	1	auth.login	staff	1	{}	2026-07-23 23:44:51.917662
11	8	1	auth.login	staff	1	{}	2026-07-23 23:45:07.921901
12	8	1	auth.login	staff	1	{}	2026-07-23 23:46:44.82789
13	8	1	auth.login	staff	1	{}	2026-07-23 23:46:45.619193
14	8	1	auth.login	staff	1	{}	2026-07-23 23:47:55.224488
15	8	1	auth.login	staff	1	{}	2026-07-23 23:50:21.617519
16	8	1	auth.login	staff	1	{}	2026-07-23 23:50:58.925603
17	8	1	auth.login	staff	1	{}	2026-07-23 23:51:28.53049
18	8	1	auth.login	staff	1	{}	2026-07-23 23:51:49.523411
19	8	1	auth.login	staff	1	{}	2026-07-23 23:52:07.72243
20	8	1	auth.login	staff	1	{}	2026-07-23 23:52:29.922556
21	8	1	auth.login	staff	1	{}	2026-07-23 23:56:28.799922
22	8	1	trip.create	trip	5	{}	2026-07-23 23:57:53.217967
23	8	1	auth.login	staff	1	{}	2026-07-24 00:34:28.449463
24	8	2	auth.login	staff	2	{}	2026-07-24 00:34:29.150603
25	8	3	auth.admin_pin_recovery	staff	3	{"method": "one_time_recovery_token"}	2026-07-24 04:51:08.138627
26	8	3	auth.login	staff	3	{}	2026-07-24 04:51:14.711535
27	8	3	auth.login	staff	3	{}	2026-07-24 04:52:56.585598
28	8	3	auth.login	staff	3	{}	2026-07-24 04:56:22.772776
29	8	3	organization.update	organization	8	{"name": "植竹幼稚園"}	2026-07-24 05:02:57.62025
30	8	3	auth.login	staff	3	{}	2026-07-24 05:09:32.773453
31	8	3	trip.create	trip	6	{}	2026-07-24 05:10:09.889266
32	8	1	auth.login	staff	1	{}	2026-07-24 05:10:34.677533
33	8	3	auth.login	staff	3	{}	2026-07-24 05:55:54.391429
34	8	3	auth.login	staff	3	{}	2026-07-24 05:56:10.404215
35	8	3	vehicle.create	vehicle	2	{}	2026-07-24 05:58:48.004351
36	8	3	route.update	route	1	{"name": "植竹幼稚園 送迎便 土呂駅", "direction": "帰り", "vehicle_id": 1}	2026-07-24 06:00:41.804556
37	8	3	route.create	route	2	{}	2026-07-24 06:01:33.580675
38	8	3	auth.login	staff	3	{}	2026-07-24 07:01:29.335127
39	8	3	vehicle.create	vehicle	3	{}	2026-07-24 07:09:44.824205
40	8	3	auth.login	staff	3	{}	2026-07-24 08:17:23.776488
41	8	3	auth.login	staff	3	{}	2026-07-24 08:30:24.769376
42	8	3	auth.login	staff	3	{}	2026-07-24 08:33:23.782435
43	8	3	auth.login	staff	3	{}	2026-07-24 08:44:40.173432
44	8	3	auth.login	staff	3	{}	2026-07-24 09:18:15.956034
45	8	3	auth.login	staff	3	{}	2026-07-24 19:39:50.266774
46	8	3	trip.create	trip	7	{"route_id": 2}	2026-07-24 19:40:18.088679
47	8	3	trip.roster.update	trip	7	{"child_ids": [1, 2]}	2026-07-24 19:42:38.172699
48	8	3	trip.force_complete	trip	2	{"unconfirmed": 0, "boarded": 0, "alighted": 0}	2026-07-24 20:19:56.212298
49	8	3	trip.force_complete	trip	3	{"unconfirmed": 0, "boarded": 0, "alighted": 0}	2026-07-24 20:20:03.605391
50	8	3	trip.force_complete	trip	4	{"unconfirmed": 0, "boarded": 0, "alighted": 0}	2026-07-24 20:20:06.786958
51	8	3	trip.force_complete	trip	5	{"unconfirmed": 0, "boarded": 0, "alighted": 0}	2026-07-24 20:20:12.883564
52	8	3	trip.force_complete	trip	6	{"unconfirmed": 0, "boarded": 0, "alighted": 0}	2026-07-24 20:20:15.341974
53	8	3	trip.manual_降車	trip	7	{"child_id": 1, "child_name": "さくら ちゃん", "reason": "qr_unavailable"}	2026-07-24 20:38:38.323384
54	8	3	trip.manual_降車	trip	7	{"child_id": 2, "child_name": "はると くん", "reason": "qr_unavailable"}	2026-07-24 20:38:47.859015
55	8	3	vehicle_check.create	vehicle_check	1	{}	2026-07-24 20:39:38.975873
56	8	1	auth.login	staff	1	{}	2026-07-24 21:13:09.500775
57	8	2	trip.third_party_approval	trip	7	{"requested_by": 1}	2026-07-24 21:13:36.30882
58	8	1	trip.complete	trip	7	{}	2026-07-24 21:14:38.97866
59	8	1	trip.create	trip	8	{"route_id": 1}	2026-07-24 21:16:40.858257
60	8	3	auth.login	staff	3	{}	2026-07-24 22:43:53.628272
61	8	3	trip.cancel	trip	8	{"reason": "vehicle_reselection"}	2026-07-24 22:51:00.566865
62	8	3	trip.create	trip	9	{"route_id": 2}	2026-07-24 22:51:04.966941
63	8	3	trip.cancel	trip	9	{"reason": "vehicle_reselection"}	2026-07-24 22:51:27.978981
64	8	3	trip.create	trip	10	{"route_id": 1}	2026-07-24 22:52:40.308101
65	8	3	trip.manual_降車	trip	10	{"child_id": 1, "child_name": "さくら ちゃん", "reason": "qr_unavailable"}	2026-07-24 22:52:51.806178
66	8	3	trip.manual_降車	trip	10	{"child_id": 2, "child_name": "はると くん", "reason": "qr_unavailable"}	2026-07-24 22:53:00.836389
67	8	3	vehicle_check.create	vehicle_check	3	{}	2026-07-24 22:53:29.969879
68	8	2	trip.third_party_approval	trip	10	{"requested_by": 3}	2026-07-24 22:54:55.636963
69	8	3	trip.complete	trip	10	{}	2026-07-24 22:54:58.090137
70	8	3	trip.create	trip	11	{"route_id": 2}	2026-07-24 23:02:49.393183
71	8	3	trip.cancel	trip	11	{"reason": "vehicle_reselection"}	2026-07-24 23:02:57.63528
72	8	3	trip.create	trip	12	{"route_id": 1}	2026-07-24 23:03:00.6886
73	8	3	trip.cancel	trip	12	{"reason": "vehicle_reselection"}	2026-07-24 23:17:51.769716
74	8	3	trip.create	trip	13	{"route_id": 2}	2026-07-24 23:30:13.890706
75	8	3	trip.cancel	trip	13	{"reason": "vehicle_reselection"}	2026-07-24 23:30:22.386498
76	8	3	trip.create	trip	14	{"route_id": 2}	2026-07-25 01:30:02.937866
77	8	3	trip.cancel	trip	14	{"reason": "vehicle_reselection"}	2026-07-25 01:30:19.359969
78	8	3	auth.login	staff	3	{}	2026-07-25 01:32:52.476697
79	8	3	trip.create	trip	15	{"route_id": 1}	2026-07-25 01:33:24.272846
80	8	3	trip.cancel	trip	15	{"reason": "vehicle_reselection"}	2026-07-25 01:35:20.144077
81	8	3	trip.create	trip	16	{"route_id": 1}	2026-07-25 01:36:02.572673
82	8	3	route.create	route	3	{"child_ids": []}	2026-07-25 01:47:11.853017
83	8	3	trip.cancel	trip	16	{"reason": "vehicle_reselection"}	2026-07-25 01:55:27.999974
84	8	3	trip.create	trip	17	{"route_id": 3}	2026-07-25 01:55:41.889421
85	8	1	auth.login	staff	1	{}	2026-07-25 01:57:05.588035
86	8	1	trip.cancel	trip	17	{"reason": "vehicle_reselection"}	2026-07-25 01:57:32.282044
87	8	3	auth.login	staff	3	{}	2026-07-25 01:59:27.784962
88	8	3	trip.create	trip	18	{"route_id": 3}	2026-07-25 04:36:42.47255
89	8	3	auth.login	staff	3	{}	2026-07-25 06:32:12.499734
173	8	3	trip.create	trip	29	{"route_id": 2}	2026-07-26 07:28:48.550394
90	8	3	trip.manual_乗車	trip	18	{"child_id": 1, "child_name": "さくら ちゃん", "reason": "qr_unavailable"}	2026-07-25 06:32:57.055544
91	8	3	trip.manual_乗車	trip	18	{"child_id": 2, "child_name": "はると くん", "reason": "qr_unavailable"}	2026-07-25 06:33:06.375103
92	8	3	auth.login	staff	3	{}	2026-07-25 08:25:09.630559
93	8	3	auth.login	staff	3	{}	2026-07-25 08:25:09.730055
94	8	3	auth.login	staff	3	{}	2026-07-25 08:25:10.430217
95	8	3	trip.manual_降車	trip	18	{"child_id": 1, "child_name": "さくら ちゃん", "reason": "qr_unavailable"}	2026-07-25 08:25:47.108933
96	8	3	trip.manual_降車	trip	18	{"child_id": 2, "child_name": "はると くん", "reason": "qr_unavailable"}	2026-07-25 08:25:52.069276
97	8	3	vehicle_check.create	vehicle_check	5	{}	2026-07-25 08:26:48.45677
98	8	2	trip.third_party_approval	trip	18	{"requested_by": 3}	2026-07-25 08:27:23.334576
99	8	3	trip.complete	trip	18	{}	2026-07-25 08:27:28.126372
100	8	3	auth.login	staff	3	{}	2026-07-25 09:00:27.795584
101	8	3	route.update	route	3	{"child_ids": [1, 2]}	2026-07-25 09:14:06.991041
102	8	3	route.update	route	3	{"child_ids": [1, 2]}	2026-07-25 09:14:28.314727
103	8	3	auth.login	staff	3	{}	2026-07-25 20:11:03.593777
104	8	3	vehicle.delete	vehicle	3	{"name": "１号車", "detached_route_ids": []}	2026-07-25 20:50:20.852053
105	8	3	route.update	route	3	{"child_ids": [1, 2]}	2026-07-25 20:50:40.650716
106	8	3	route.create	route	4	{"child_ids": []}	2026-07-25 20:52:39.392271
107	8	3	route.update	route	3	{"name": "植竹幼稚園　1号車（先出し）　行き"}	2026-07-25 21:14:03.662739
108	8	3	route.update	route	3	{"name": "1号車（土呂駅：先出し）　行き"}	2026-07-25 21:15:43.615951
109	8	3	route.update	route	4	{"name": "２号車（植竹地区：先出し）　行き"}	2026-07-25 21:16:55.13278
110	8	3	auth.login	staff	3	{}	2026-07-25 22:25:41.502755
111	8	3	child.create	child	3	{}	2026-07-25 22:27:37.015245
112	8	3	route.update	route	4	{"child_ids": [3]}	2026-07-25 22:29:58.011892
113	8	3	route.update	route	2	{"child_ids": [3]}	2026-07-25 22:30:21.881569
114	8	3	auth.login	staff	3	{}	2026-07-25 22:32:43.017057
115	8	3	auth.login	staff	3	{}	2026-07-25 22:34:07.312099
116	8	3	trip.create	trip	19	{"route_id": 3}	2026-07-25 22:45:28.93507
117	8	3	trip.cancel	trip	19	{"reason": "vehicle_reselection"}	2026-07-25 22:45:52.920625
118	8	3	trip.create	trip	20	{"route_id": 4}	2026-07-25 22:45:56.439593
119	8	3	trip.manual_乗車	trip	20	{"child_id": 3, "child_name": "つきくん", "reason": "qr_unavailable"}	2026-07-25 22:46:23.410377
120	8	3	trip.manual_降車	trip	20	{"child_id": 3, "child_name": "つきくん", "reason": "qr_unavailable"}	2026-07-25 22:46:47.620298
121	8	3	vehicle_check.create	vehicle_check	7	{}	2026-07-25 22:47:21.729589
122	8	2	trip.third_party_approval	trip	20	{"requested_by": 3}	2026-07-25 22:47:35.915009
123	8	3	trip.complete	trip	20	{}	2026-07-25 22:47:47.521042
124	8	3	trip.create	trip	21	{"route_id": 4}	2026-07-25 22:48:47.829398
125	8	3	trip.create	trip	22	{"route_id": 4}	2026-07-25 22:55:31.361568
126	8	3	trip.乗車	trip	22	{"child_id": 3}	2026-07-25 22:56:33.716711
127	8	3	trip.降車	trip	22	{"child_id": 3}	2026-07-25 23:06:03.75107
128	8	3	vehicle_check.create	vehicle_check	9	{}	2026-07-25 23:26:58.873504
129	8	2	trip.third_party_approval	trip	22	{"requested_by": 3}	2026-07-25 23:27:28.608361
130	8	3	trip.complete	trip	22	{}	2026-07-25 23:27:31.365597
131	8	3	trip.乗車	trip	21	{"child_id": 3}	2026-07-25 23:28:46.145121
132	8	3	trip.降車	trip	21	{"child_id": 3}	2026-07-25 23:28:52.781956
133	8	3	vehicle_check.create	vehicle_check	11	{}	2026-07-25 23:29:38.350537
134	8	2	trip.third_party_approval	trip	21	{"requested_by": 3}	2026-07-25 23:29:57.807898
135	8	3	trip.complete	trip	21	{}	2026-07-25 23:29:59.923663
136	8	3	trip.create	trip	23	{"route_id": 3}	2026-07-25 23:55:09.940035
137	8	3	trip.cancel	trip	23	{"reason": "vehicle_reselection"}	2026-07-25 23:55:33.020395
138	8	3	trip.create	trip	24	{"route_id": 2}	2026-07-25 23:55:38.619685
139	8	3	trip.降車	trip	24	{"child_id": 3}	2026-07-26 01:23:18.24606
140	8	3	vehicle_check.create	vehicle_check	13	{}	2026-07-26 01:23:43.631294
141	8	3	vehicle_check.create	vehicle_check	14	{}	2026-07-26 01:23:43.729621
142	8	2	trip.third_party_approval	trip	24	{"requested_by": 3}	2026-07-26 01:24:05.532082
143	8	3	trip.complete	trip	24	{}	2026-07-26 01:24:08.905214
144	8	3	trip.create	trip	25	{"route_id": 3}	2026-07-26 02:21:55.942156
145	8	3	trip.cancel	trip	25	{"reason": "vehicle_reselection"}	2026-07-26 02:22:01.370854
146	8	3	trip.create	trip	26	{"route_id": 2}	2026-07-26 02:22:03.282641
147	8	3	trip.manual_降車	trip	26	{"child_id": 3, "child_name": "つきくん", "reason": "qr_unavailable"}	2026-07-26 02:22:39.498443
148	8	3	vehicle_check.create	vehicle_check	16	{}	2026-07-26 02:23:17.41287
149	8	3	vehicle_check.create	vehicle_check	17	{}	2026-07-26 02:23:17.484693
150	8	3	video.upload	video	1	{"size": 1764688, "duration_seconds": 6}	2026-07-26 03:33:28.37703
151	8	3	video.analyze.request	video	1	{}	2026-07-26 03:33:28.6791
152	8	2	trip.third_party_approval	trip	26	{"requested_by": 3}	2026-07-26 03:33:56.607896
153	8	3	trip.complete	trip	26	{}	2026-07-26 03:33:59.227234
154	8	3	trip.create	trip	27	{"route_id": 2}	2026-07-26 03:56:16.926015
155	8	3	trip.manual_降車	trip	27	{"child_id": 3, "child_name": "つきくん", "reason": "qr_unavailable"}	2026-07-26 03:56:32.311513
156	8	3	vehicle_check.create	vehicle_check	19	{}	2026-07-26 03:56:58.815731
157	8	3	vehicle_check.create	vehicle_check	20	{}	2026-07-26 03:56:58.816105
158	8	3	video.upload	video	2	{"size": 325203, "duration_seconds": 7}	2026-07-26 04:10:12.962461
159	8	3	video.analyze.request	video	2	{}	2026-07-26 04:10:13.211994
160	8	2	trip.third_party_approval	trip	27	{"requested_by": 3}	2026-07-26 04:11:02.505416
161	8	3	trip.complete	trip	27	{}	2026-07-26 04:11:11.350978
162	8	3	trip.create	trip	28	{"route_id": 2}	2026-07-26 04:36:11.168536
163	8	3	trip.manual_降車	trip	28	{"child_id": 3, "child_name": "つきくん", "reason": "qr_unavailable"}	2026-07-26 04:36:27.274674
164	8	3	vehicle_check.create	vehicle_check	22	{}	2026-07-26 04:36:45.240858
165	8	3	vehicle_check.create	vehicle_check	23	{}	2026-07-26 04:36:45.243012
166	8	3	video.upload	video	3	{"size": 291978, "duration_seconds": 6}	2026-07-26 04:37:05.819453
167	8	3	video.analyze.request	video	3	{}	2026-07-26 04:37:06.128948
168	8	2	trip.third_party_approval	trip	28	{"requested_by": 3}	2026-07-26 04:37:18.617935
169	8	3	trip.complete	trip	28	{}	2026-07-26 04:37:23.604204
170	8	3	video.download	video	3	{}	2026-07-26 04:37:36.730602
171	8	3	video.download	video	3	{}	2026-07-26 04:38:23.653573
172	8	3	auth.login	staff	3	{}	2026-07-26 06:35:33.474451
174	8	3	trip.cancel	trip	29	{"reason": "vehicle_reselection"}	2026-07-26 07:29:08.120223
175	8	3	trip.create	trip	30	{"route_id": 1}	2026-07-26 07:29:20.681083
176	8	1	auth.login	staff	1	{}	2026-07-27 02:34:05.998238
177	8	1	trip.cancel	trip	30	{"reason": "vehicle_reselection"}	2026-07-27 02:34:35.797234
178	8	1	trip.create	trip	31	{"route_id": 2}	2026-07-27 02:34:38.300421
179	8	1	trip.create	trip	32	{"route_id": 2}	2026-07-27 02:36:25.205869
180	8	3	auth.login	staff	3	{}	2026-07-27 08:18:12.737402
181	8	3	auth.login	staff	3	{}	2026-07-27 08:20:23.755618
182	8	3	trip.manual_降車	trip	32	{"child_id": 3, "child_name": "つきくん", "reason": "qr_unavailable"}	2026-07-27 08:26:48.803218
183	8	3	notification.event.create	trip	32	{"event_key": "org:8:trip:32:child:3:alighted", "child_id": 3, "created": 0, "channels": []}	2026-07-27 08:26:48.80322
184	8	3	auth.login	staff	3	{}	2026-07-27 08:37:00.138151
185	8	3	guardian_contact.create	guardian_contact	1	{"child_ids": [3], "email_enabled": true, "line_enabled": true, "consent": true}	2026-07-27 08:40:02.624875
186	8	3	line.link.request.issue	line_link_request	1	{"guardian_contact_id": 1, "expires_at": "2026-07-28T08:40:59.815022", "email_notification_id": 1, "email_status": "failed"}	2026-07-27 08:41:00.839445
187	8	3	guardian_contact.update	guardian_contact	1	{"email_enabled": true, "line_enabled": false}	2026-07-27 08:44:21.49995
188	8	3	guardian_contact.update	guardian_contact	1	{"email_enabled": true, "line_enabled": true}	2026-07-27 08:55:46.16495
189	8	3	trip.create	trip	33	{"route_id": 2}	2026-07-27 08:58:41.379526
190	8	3	trip.降車	trip	33	{"child_id": 3}	2026-07-27 08:59:20.600895
191	8	3	notification.event.create	trip	33	{"event_key": "org:8:trip:33:child:3:alighted", "child_id": 3, "created": 1, "channels": ["email"]}	2026-07-27 08:59:20.604774
192	8	3	trip.create	trip	34	{"route_id": 2}	2026-07-27 09:32:37.178952
193	8	3	trip.降車	trip	34	{"child_id": 3}	2026-07-27 09:33:15.63683
194	8	3	notification.event.create	trip	34	{"event_key": "org:8:trip:34:child:3:alighted", "child_id": 3, "created": 1, "channels": ["email"]}	2026-07-27 09:33:15.642703
195	8	3	trip.create	trip	35	{"route_id": 2}	2026-07-27 09:40:53.16112
196	8	3	trip.降車	trip	35	{"child_id": 3}	2026-07-27 09:41:05.117859
197	8	3	notification.event.create	trip	35	{"event_key": "org:8:trip:35:child:3:alighted", "child_id": 3, "created": 1, "channels": ["email"]}	2026-07-27 09:41:05.121711
198	8	3	trip.create	trip	36	{"route_id": 2}	2026-07-27 09:53:51.267288
199	8	3	trip.降車	trip	36	{"child_id": 3}	2026-07-27 09:54:04.565727
200	8	3	notification.event.create	trip	36	{"event_key": "org:8:trip:36:child:3:alighted", "child_id": 3, "created": 1, "channels": ["email"]}	2026-07-27 09:54:04.571211
201	8	3	line.link.request.issue	line_link_request	2	{"guardian_contact_id": 1, "expires_at": "2026-07-28T09:57:02.723077", "email_notification_id": 6, "email_status": "failed"}	2026-07-27 09:57:03.11702
202	8	3	trip.create	trip	37	{"route_id": 2}	2026-07-27 09:59:39.117491
203	8	3	trip.降車	trip	37	{"child_id": 3}	2026-07-27 09:59:49.082287
204	8	3	notification.event.create	trip	37	{"event_key": "org:8:trip:37:child:3:alighted", "child_id": 3, "created": 1, "channels": ["email"]}	2026-07-27 09:59:49.088719
205	8	3	trip.create	trip	38	{"route_id": 2}	2026-07-27 10:23:53.960069
206	8	3	trip.降車	trip	38	{"child_id": 3}	2026-07-27 10:24:11.069557
207	8	3	notification.event.create	trip	38	{"event_key": "org:8:trip:38:child:3:alighted", "child_id": 3, "created": 1, "channels": ["email"]}	2026-07-27 10:24:11.087408
208	8	3	line.link.request.issue	line_link_request	3	{"guardian_contact_id": 1, "expires_at": "2026-07-28T10:27:42.210846", "email_notification_id": 9, "email_status": "failed"}	2026-07-27 10:27:42.555722
209	8	3	line.link.request.issue	line_link_request	4	{"guardian_contact_id": 1, "expires_at": "2026-07-28T10:45:40.274574", "email_notification_id": 10, "email_status": "failed"}	2026-07-27 10:45:40.695658
210	8	3	trip.create	trip	39	{"route_id": 2}	2026-07-27 10:49:40.655947
211	8	3	line.link.request.issue	line_link_request	5	{"guardian_contact_id": 1, "expires_at": "2026-07-28T10:50:17.127067", "email_notification_id": 11, "email_status": "failed"}	2026-07-27 10:50:17.192317
212	8	3	auth.login	staff	3	{}	2026-07-27 20:04:27.510437
213	8	3	auth.login	staff	3	{}	2026-07-27 20:05:05.213964
214	8	3	trip.create	trip	40	{"route_id": 2}	2026-07-27 20:05:13.420953
215	8	3	line.link.request.issue	line_link_request	6	{"guardian_contact_id": 1, "expires_at": "2026-07-28T20:05:39.379068", "email_notification_id": 12, "email_status": "failed"}	2026-07-27 20:05:39.719172
216	8	3	line.link.request.issue	line_link_request	7	{"guardian_contact_id": 1, "expires_at": "2026-07-28T20:29:59.944813", "email_notification_id": 13, "email_status": "failed"}	2026-07-27 20:30:00.014928
217	8	\N	line.contact.link	guardian_contact	1	{"line_contact_id": 3, "line_link_request_id": 7}	2026-07-27 21:04:30.872649
218	8	3	trip.降車	trip	40	{"child_id": 3}	2026-07-27 21:06:26.326954
219	8	3	notification.event.create	trip	40	{"event_key": "org:8:trip:40:child:3:alighted", "child_id": 3, "created": 2, "channels": ["email", "line"]}	2026-07-27 21:06:26.337034
220	8	3	auth.login	staff	3	{}	2026-07-27 21:25:11.87895
221	8	3	trip.create	trip	41	{"route_id": 2}	2026-07-27 22:53:42.304631
222	8	3	trip.降車	trip	41	{"child_id": 3}	2026-07-27 22:54:08.588674
223	8	3	notification.event.create	trip	41	{"event_key": "org:8:trip:41:child:3:alighted", "child_id": 3, "created": 2, "channels": ["email", "line"]}	2026-07-27 22:54:09.398272
224	8	3	notification.dispatch	notification	16	{"status": "failed", "channel": "email", "attempt_count": 2}	2026-07-27 22:59:48.587498
225	8	3	notification.dispatch	notification	16	{"status": "failed", "channel": "email", "attempt_count": 3}	2026-07-27 23:11:17.718593
226	8	3	notification.dispatch	notification	16	{"status": "sent", "channel": "email", "attempt_count": 4}	2026-07-27 23:20:27.130827
227	8	3	auth.login	staff	3	{}	2026-07-27 23:36:25.056434
228	8	3	auth.login	staff	3	{}	2026-07-28 07:23:46.892258
229	8	3	guardian_contact.create	guardian_contact	2	{"child_ids": [1], "email_enabled": true, "line_enabled": true, "consent": true}	2026-07-28 07:27:57.622512
230	8	3	line.link.request.issue	line_link_request	8	{"guardian_contact_id": 2, "expires_at": "2026-07-29T07:28:35.729569", "email_notification_id": 18, "email_status": "sent"}	2026-07-28 07:28:38.427785
231	8	3	trip.create	trip	42	{"route_id": 2}	2026-07-28 07:33:49.968873
232	8	3	auth.login	staff	3	{}	2026-07-28 20:30:59.086371
233	8	3	auth.login	staff	3	{}	2026-07-28 20:32:19.283481
234	8	3	guardian_contact.update	guardian_contact	1	{"name": "ママ", "email_enabled": true, "line_enabled": true, "consent": true, "child_ids": [3, 1], "relationship": "ままママ", "notify_alighted": true}	2026-07-28 20:46:01.195807
235	8	3	auth.login	staff	3	{}	2026-07-28 22:53:21.734247
236	8	3	trip.create	trip	43	{"route_id": 2}	2026-07-28 22:55:45.476942
237	8	3	trip.降車	trip	43	{"child_id": 3}	2026-07-28 22:57:06.090839
238	8	3	notification.event.create	trip	43	{"event_key": "org:8:trip:43:child:3:alighted", "child_id": 3, "created": 2, "channels": ["email", "line"]}	2026-07-28 22:57:08.769402
239	8	3	vehicle_check.create	vehicle_check	25	{}	2026-07-28 23:04:54.669345
240	8	3	video.upload	video	4	{"size": 591475, "duration_seconds": 7}	2026-07-28 23:05:29.292585
241	8	3	video.analyze.request	video	4	{}	2026-07-28 23:05:29.476751
242	8	2	trip.third_party_approval	trip	43	{"requested_by": 3}	2026-07-28 23:06:00.435291
243	8	3	trip.complete	trip	43	{}	2026-07-28 23:06:02.894817
244	8	3	auth.login	staff	3	{}	2026-07-28 23:37:53.280796
245	8	3	auth.login	staff	3	{}	2026-07-28 23:37:53.491919
246	8	3	auth.login	staff	3	{}	2026-07-29 00:02:35.196443
247	8	3	auth.login	staff	3	{}	2026-07-29 00:02:35.499044
248	8	3	trip.降車	trip	42	{"child_id": 3}	2026-07-29 00:04:37.837946
249	8	3	notification.event.create	trip	42	{"event_key": "org:8:trip:42:child:3:alighted", "child_id": 3, "created": 2, "channels": ["email", "line"]}	2026-07-29 00:04:39.827118
250	8	3	vehicle_check.create	vehicle_check	27	{}	2026-07-29 00:05:06.639834
251	8	3	vehicle_check.create	vehicle_check	28	{}	2026-07-29 00:05:06.640241
252	8	3	video.upload	video	5	{"size": 530051, "duration_seconds": 6}	2026-07-29 00:05:30.491347
253	8	3	video.analyze.request	video	5	{}	2026-07-29 00:05:30.840973
254	8	2	trip.third_party_approval	trip	42	{"requested_by": 3}	2026-07-29 00:05:51.726929
255	8	3	trip.complete	trip	42	{}	2026-07-29 00:05:54.546807
256	8	3	trip.create	trip	44	{"route_id": 3}	2026-07-29 00:06:03.362461
257	8	3	trip.乗車	trip	44	{"child_id": 1}	2026-07-29 00:06:21.57672
258	8	3	trip.manual_乗車	trip	44	{"child_id": 2, "child_name": "はると くん", "reason": "qr_unavailable"}	2026-07-29 02:14:28.847118
259	8	3	trip.manual_降車	trip	44	{"child_id": 1, "child_name": "さくら ちゃん", "reason": "qr_unavailable"}	2026-07-29 02:15:23.943851
260	8	3	notification.event.create	trip	44	{"event_key": "org:8:trip:44:child:1:alighted", "child_id": 1, "created": 3, "channels": ["email", "line", "email"]}	2026-07-29 02:15:27.263514
261	8	3	trip.manual_降車	trip	44	{"child_id": 2, "child_name": "はると くん", "reason": "qr_unavailable"}	2026-07-29 02:15:52.24997
262	8	3	notification.event.create	trip	44	{"event_key": "org:8:trip:44:child:2:alighted", "child_id": 2, "created": 0, "channels": []}	2026-07-29 02:15:52.249972
263	8	3	vehicle_check.create	vehicle_check	30	{}	2026-07-29 02:18:55.107037
264	8	2	trip.third_party_approval	trip	44	{"requested_by": 3}	2026-07-29 02:42:14.667101
265	8	3	trip.complete	trip	44	{}	2026-07-29 02:42:24.126644
266	8	3	trip.create	trip	45	{"route_id": 3}	2026-07-29 02:42:27.99018
267	8	3	trip.cancel	trip	45	{"reason": "vehicle_reselection"}	2026-07-29 02:42:37.178306
268	8	3	trip.create	trip	46	{"route_id": 2}	2026-07-29 02:42:39.252407
269	8	3	trip.manual_降車	trip	46	{"child_id": 3, "child_name": "つきくん", "reason": "qr_unavailable"}	2026-07-29 02:42:58.701385
270	8	3	notification.event.create	trip	46	{"event_key": "org:8:trip:46:child:3:alighted", "child_id": 3, "created": 2, "channels": ["email", "line"]}	2026-07-29 02:43:00.681716
271	8	3	vehicle_check.create	vehicle_check	32	{}	2026-07-29 02:43:05.251247
272	8	3	trip.complete	trip	46	{}	2026-07-29 03:38:54.946628
273	8	3	trip.create	trip	47	{"route_id": 2}	2026-07-29 03:38:58.077261
274	8	3	trip.降車	trip	47	{"child_id": 3}	2026-07-29 03:39:31.016998
275	8	3	notification.event.create	trip	47	{"event_key": "org:8:trip:47:child:3:alighted", "child_id": 3, "created": 2, "channels": ["email", "line"]}	2026-07-29 03:39:33.244725
276	8	3	vehicle_check.create	vehicle_check	33	{}	2026-07-29 03:39:53.114804
277	8	3	trip.complete	trip	47	{}	2026-07-29 03:39:53.348453
278	8	3	trip.create	trip	48	{"route_id": 2}	2026-07-29 03:39:55.901777
279	8	3	trip.降車	trip	48	{"child_id": 3}	2026-07-29 03:55:52.135474
280	8	3	notification.event.create	trip	48	{"event_key": "org:8:trip:48:child:3:alighted", "child_id": 3, "created": 2, "channels": ["email", "line"]}	2026-07-29 03:55:54.080062
281	8	3	video.upload	video	6	{"size": 482309, "duration_seconds": 6}	2026-07-29 03:56:15.789545
282	8	3	video.analyze.request	video	6	{}	2026-07-29 03:56:16.088264
283	8	3	vehicle_check.create	vehicle_check	34	{}	2026-07-29 03:56:16.267815
284	8	3	trip.complete	trip	48	{}	2026-07-29 03:56:16.436666
285	8	3	trip.create	trip	49	{"route_id": 2}	2026-07-29 03:56:27.749275
286	8	3	trip.cancel	trip	49	{"reason": "vehicle_reselection"}	2026-07-29 03:56:54.879629
287	8	3	trip.create	trip	50	{"route_id": 2}	2026-07-29 03:57:32.127611
288	8	3	trip.cancel	trip	50	{"reason": "vehicle_reselection"}	2026-07-29 04:07:35.917475
289	8	3	trip.create	trip	51	{"route_id": 2}	2026-07-29 04:08:08.47178
290	8	3	trip.manual_降車	trip	51	{"child_id": 3, "child_name": "つきくん", "reason": "qr_unavailable"}	2026-07-29 04:08:21.907598
291	8	3	notification.event.create	trip	51	{"event_key": "org:8:trip:51:child:3:alighted", "child_id": 3, "created": 2, "channels": ["email", "line"]}	2026-07-29 04:08:23.588119
292	8	3	video.upload	video	7	{"size": 468822, "duration_seconds": 6}	2026-07-29 04:08:56.871802
293	8	3	video.analyze.request	video	7	{}	2026-07-29 04:08:57.038742
294	8	3	vehicle_check.create	vehicle_check	35	{}	2026-07-29 04:08:57.247769
295	8	3	trip.complete	trip	51	{}	2026-07-29 04:08:57.404578
296	8	3	trip.create	trip	52	{"route_id": 2}	2026-07-29 04:09:03.2548
297	8	3	trip.manual_降車	trip	52	{"child_id": 3, "child_name": "つきくん", "reason": "qr_unavailable"}	2026-07-29 04:09:32.749757
298	8	3	notification.event.create	trip	52	{"event_key": "org:8:trip:52:child:3:alighted", "child_id": 3, "created": 2, "channels": ["email", "line"]}	2026-07-29 04:09:34.419373
299	8	3	video.upload	video	8	{"size": 508527, "duration_seconds": 6}	2026-07-29 04:10:43.194406
300	8	3	video.analyze.request	video	8	{}	2026-07-29 04:10:43.427451
301	8	3	vehicle_check.create	vehicle_check	36	{}	2026-07-29 04:10:43.598343
302	8	3	trip.complete	trip	52	{}	2026-07-29 04:10:43.747312
303	8	3	trip.create	trip	53	{"route_id": 2}	2026-07-29 04:10:52.997277
304	8	3	auth.login	staff	3	{}	2026-07-29 04:43:20.068654
305	8	3	auth.login	staff	3	{}	2026-07-29 04:43:20.18301
306	8	3	trip.manual_降車	trip	53	{"child_id": 3, "child_name": "つきくん", "reason": "qr_unavailable"}	2026-07-29 04:44:02.068969
307	8	3	notification.event.create	trip	53	{"event_key": "org:8:trip:53:child:3:alighted", "child_id": 3, "created": 2, "channels": ["email", "line"]}	2026-07-29 04:44:08.293101
308	8	3	video.upload	video	9	{"size": 474534, "duration_seconds": 6}	2026-07-29 04:44:31.105551
309	8	3	video.analyze.request	video	9	{}	2026-07-29 04:44:31.274786
310	8	3	video.download	video	9	{}	2026-07-29 04:44:51.419497
311	8	3	trip.create	trip	54	{"route_id": 2}	2026-07-29 04:45:14.565078
312	8	3	trip.manual_降車	trip	54	{"child_id": 3, "child_name": "つきくん", "reason": "qr_unavailable"}	2026-07-29 04:45:28.67516
313	8	3	notification.event.create	trip	54	{"event_key": "org:8:trip:54:child:3:alighted", "child_id": 3, "created": 2, "channels": ["email", "line"]}	2026-07-29 04:45:30.404864
314	8	3	video.upload	video	10	{"size": 472093, "duration_seconds": 6}	2026-07-29 04:45:50.86746
315	8	3	video.analyze.request	video	10	{}	2026-07-29 04:45:51.053936
316	8	3	vehicle_check.create	vehicle_check	37	{}	2026-07-29 04:45:54.709478
317	8	3	trip.complete	trip	54	{}	2026-07-29 04:45:55.021525
318	8	3	trip.create	trip	55	{"route_id": 2}	2026-07-29 04:46:00.159286
319	8	3	trip.manual_降車	trip	55	{"child_id": 3, "child_name": "つきくん", "reason": "qr_unavailable"}	2026-07-29 04:46:45.316159
320	8	3	notification.event.create	trip	55	{"event_key": "org:8:trip:55:child:3:alighted", "child_id": 3, "created": 2, "channels": ["email", "line"]}	2026-07-29 04:46:46.95442
321	8	3	video.upload	video	11	{"size": 455624, "duration_seconds": 6}	2026-07-29 04:47:23.024678
322	8	3	video.analyze.request	video	11	{}	2026-07-29 04:47:23.320725
323	8	3	vehicle_check.create	vehicle_check	38	{}	2026-07-29 05:02:53.964303
324	8	3	trip.complete	trip	55	{}	2026-07-29 05:02:54.141416
325	8	3	trip.create	trip	56	{"route_id": 2}	2026-07-29 05:03:06.274216
326	8	3	trip.manual_降車	trip	56	{"child_id": 3, "child_name": "つきくん", "reason": "qr_unavailable"}	2026-07-29 05:04:03.581871
327	8	3	notification.event.create	trip	56	{"event_key": "org:8:trip:56:child:3:alighted", "child_id": 3, "created": 2, "channels": ["email", "line"]}	2026-07-29 05:04:05.336549
328	8	3	video.upload	video	12	{"size": 449169, "duration_seconds": 6}	2026-07-29 05:04:28.819369
329	8	3	video.analyze.request	video	12	{}	2026-07-29 05:04:29.450233
330	8	3	vehicle_check.create	vehicle_check	39	{}	2026-07-29 05:04:45.376162
331	8	3	trip.complete	trip	56	{}	2026-07-29 05:04:45.969751
332	8	3	trip.create	trip	57	{"route_id": 4}	2026-07-29 05:10:39.285743
333	8	3	trip.cancel	trip	57	{"reason": "vehicle_reselection"}	2026-07-29 05:10:45.514954
334	8	3	trip.create	trip	58	{"route_id": 1}	2026-07-29 05:10:47.754263
335	8	3	trip.降車	trip	58	{"child_id": 1}	2026-07-29 05:11:15.479224
336	8	3	notification.event.create	trip	58	{"event_key": "org:8:trip:58:child:1:alighted", "child_id": 1, "created": 3, "channels": ["email", "line", "email"]}	2026-07-29 05:11:19.113668
337	8	3	trip.manual_降車	trip	58	{"child_id": 2, "child_name": "はると くん", "reason": "qr_unavailable"}	2026-07-29 05:11:35.625668
338	8	3	notification.event.create	trip	58	{"event_key": "org:8:trip:58:child:2:alighted", "child_id": 2, "created": 0, "channels": []}	2026-07-29 05:11:35.625671
339	8	3	video.upload	video	13	{"size": 468783, "duration_seconds": 6}	2026-07-29 05:12:35.395754
340	8	3	video.analyze.request	video	13	{}	2026-07-29 05:12:35.761806
341	8	3	vehicle_check.create	vehicle_check	40	{}	2026-07-29 05:12:36.227328
342	8	3	trip.complete	trip	58	{}	2026-07-29 05:12:36.730658
343	8	3	auth.login	staff	3	{}	2026-07-30 04:07:43.154005
344	8	3	auth.login	staff	3	{}	2026-07-30 04:21:21.053761
345	8	3	auth.login	staff	3	{}	2026-07-30 21:38:12.209587
346	8	3	auth.login	staff	3	{}	2026-07-30 21:57:26.950059
347	8	3	auth.login	staff	3	{}	2026-07-30 21:57:27.453111
348	8	3	auth.login	staff	3	{}	2026-07-31 00:04:57.912321
349	8	3	auth.login	staff	3	{}	2026-07-31 00:04:58.312187
350	8	3	auth.login	staff	3	{}	2026-07-31 00:06:38.005512
351	8	3	auth.login	staff	3	{}	2026-07-31 00:22:08.205789
352	8	3	auth.login	staff	3	{}	2026-07-31 00:22:08.609325
353	8	3	auth.login	staff	3	{}	2026-08-03 01:54:08.061377
354	8	3	auth.login	staff	3	{}	2026-08-03 01:54:08.466344
355	8	3	video.upload	video	14	{"size": 477983, "duration_seconds": 6}	2026-08-03 01:55:09.641383
356	8	3	video.analyze.request	video	14	{}	2026-08-03 01:55:09.794054
357	8	3	vehicle_check.create	vehicle_check	41	{}	2026-08-03 01:55:13.544843
358	8	3	trip.complete	trip	53	{}	2026-08-03 01:55:13.692857
359	8	3	auth.login	staff	3	{}	2026-08-03 23:28:10.953941
360	8	3	video.upload	video	15	{"size": 463441, "duration_seconds": 10}	2026-08-03 23:29:15.403156
361	8	3	video.analyze.request	video	15	{}	2026-08-03 23:29:15.679082
362	8	3	vehicle_check.create	vehicle_check	42	{}	2026-08-03 23:29:24.524969
363	8	3	trip.complete	trip	41	{}	2026-08-03 23:29:24.963976
364	8	3	auth.login	staff	3	{}	2026-08-03 23:53:52.073767
365	8	1	auth.login	staff	1	{}	2026-08-04 00:20:47.375862
366	8	1	auth.login	staff	1	{}	2026-08-04 00:27:06.872124
367	8	1	auth.login	staff	1	{}	2026-08-04 00:27:15.87305
368	8	1	auth.login	staff	1	{}	2026-08-04 04:43:42.715524
\.


--
-- Data for Name: vehicles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.vehicles (id, name, plate_number, organization_id, is_active) FROM stdin;
1	2号車	品川 500 あ 1234	8	t
2	1号車	品川 500 い 2222	8	t
3	１号車	品川 500 い 2222	8	f
\.


--
-- Data for Name: bus_routes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.bus_routes (id, name, direction, vehicle_id, organization_id, is_active) FROM stdin;
1	植竹幼稚園 送迎便 土呂駅	帰り	1	8	t
2	植竹幼稚園 送迎便 植竹・帰り	帰り	2	8	t
3	1号車（土呂駅：先出し）　行き	往路	2	8	t
4	２号車（植竹地区：先出し）　行き	往路	1	8	t
\.


--
-- Data for Name: bus_trips; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.bus_trips (id, route_id, vehicle_id, direction, status, started_at, completed_at, organization_id) FROM stdin;
1	\N	\N	帰り	完了	2026-07-23 20:58:51.811905	2026-07-23 21:02:37.732342	8
52	2	2	帰り	完了	2026-07-29 04:09:03.250727	2026-07-29 04:10:43.747053	8
2	\N	\N	帰り	完了	2026-07-23 22:42:11.720658	2026-07-24 20:19:56.210902	8
3	\N	\N	帰り	完了	2026-07-23 22:59:09.742742	2026-07-24 20:20:03.605018	8
4	\N	\N	帰り	完了	2026-07-23 23:38:15.127665	2026-07-24 20:20:06.786667	8
5	1	1	帰り	完了	2026-07-23 23:57:53.215398	2026-07-24 20:20:12.883216	8
6	1	1	帰り	完了	2026-07-24 05:10:09.887105	2026-07-24 20:20:15.341556	8
7	2	2	帰り	完了	2026-07-24 19:40:18.08413	2026-07-24 21:14:38.978332	8
8	1	1	帰り	中止	2026-07-24 21:16:40.854628	2026-07-24 22:51:00.565483	8
9	2	2	帰り	中止	2026-07-24 22:51:04.962824	2026-07-24 22:51:27.978704	8
10	1	1	帰り	完了	2026-07-24 22:52:40.303082	2026-07-24 22:54:58.089871	8
11	2	2	帰り	中止	2026-07-24 23:02:49.390272	2026-07-24 23:02:57.634984	8
12	1	1	帰り	中止	2026-07-24 23:03:00.68565	2026-07-24 23:17:51.767865	8
13	2	2	帰り	中止	2026-07-24 23:30:13.882922	2026-07-24 23:30:22.386229	8
14	2	2	帰り	中止	2026-07-25 01:30:02.933239	2026-07-25 01:30:19.359665	8
15	1	1	帰り	中止	2026-07-25 01:33:24.269847	2026-07-25 01:35:20.143796	8
16	1	1	帰り	中止	2026-07-25 01:36:02.568694	2026-07-25 01:55:27.999701	8
17	3	2	往路	中止	2026-07-25 01:55:41.886109	2026-07-25 01:57:32.281779	8
18	3	2	往路	完了	2026-07-25 04:36:42.467649	2026-07-25 08:27:28.126104	8
19	3	2	往路	中止	2026-07-25 22:45:28.923685	2026-07-25 22:45:52.92033	8
20	4	1	往路	完了	2026-07-25 22:45:56.436547	2026-07-25 22:47:47.520712	8
22	4	1	往路	完了	2026-07-25 22:55:31.358461	2026-07-25 23:27:31.365345	8
21	4	1	往路	完了	2026-07-25 22:48:47.826425	2026-07-25 23:29:59.923293	8
23	3	2	往路	中止	2026-07-25 23:55:09.93683	2026-07-25 23:55:33.020097	8
24	2	2	帰り	完了	2026-07-25 23:55:38.616487	2026-07-26 01:24:08.904937	8
25	3	2	往路	中止	2026-07-26 02:21:55.937444	2026-07-26 02:22:01.370482	8
26	2	2	帰り	完了	2026-07-26 02:22:03.278992	2026-07-26 03:33:59.226926	8
27	2	2	帰り	完了	2026-07-26 03:56:16.920642	2026-07-26 04:11:11.350679	8
28	2	2	帰り	完了	2026-07-26 04:36:11.162842	2026-07-26 04:37:23.603873	8
29	2	2	帰り	中止	2026-07-26 07:28:48.542341	2026-07-26 07:29:08.119891	8
30	1	1	帰り	中止	2026-07-26 07:29:20.677885	2026-07-27 02:34:35.796818	8
31	2	2	帰り	運行中	2026-07-27 02:34:38.296474	\N	8
32	2	2	帰り	運行中	2026-07-27 02:36:25.199597	\N	8
33	2	2	帰り	運行中	2026-07-27 08:58:41.375998	\N	8
34	2	2	帰り	運行中	2026-07-27 09:32:37.173789	\N	8
35	2	2	帰り	運行中	2026-07-27 09:40:53.156937	\N	8
36	2	2	帰り	運行中	2026-07-27 09:53:51.256467	\N	8
37	2	2	帰り	運行中	2026-07-27 09:59:39.114	\N	8
38	2	2	帰り	運行中	2026-07-27 10:23:53.954896	\N	8
39	2	2	帰り	運行中	2026-07-27 10:49:40.652487	\N	8
40	2	2	帰り	運行中	2026-07-27 20:05:13.417054	\N	8
43	2	2	帰り	完了	2026-07-28 22:55:45.473118	2026-07-28 23:06:02.894542	8
42	2	2	帰り	完了	2026-07-28 07:33:49.965651	2026-07-29 00:05:54.546447	8
44	3	2	往路	完了	2026-07-29 00:06:03.359142	2026-07-29 02:42:24.12632	8
45	3	2	往路	中止	2026-07-29 02:42:27.986165	2026-07-29 02:42:37.178035	8
46	2	2	帰り	完了	2026-07-29 02:42:39.249413	2026-07-29 03:38:54.944061	8
47	2	2	帰り	完了	2026-07-29 03:38:58.073646	2026-07-29 03:39:53.34819	8
48	2	2	帰り	完了	2026-07-29 03:39:55.89882	2026-07-29 03:56:16.436404	8
49	2	2	帰り	中止	2026-07-29 03:56:27.744933	2026-07-29 03:56:54.879332	8
50	2	2	帰り	中止	2026-07-29 03:57:32.124215	2026-07-29 04:07:35.917114	8
51	2	2	帰り	完了	2026-07-29 04:08:08.468809	2026-07-29 04:08:57.404306	8
54	2	2	帰り	完了	2026-07-29 04:45:14.561203	2026-07-29 04:45:55.021259	8
55	2	2	帰り	完了	2026-07-29 04:46:00.156358	2026-07-29 05:02:54.141118	8
56	2	2	帰り	完了	2026-07-29 05:03:06.271239	2026-07-29 05:04:45.969448	8
57	4	1	往路	中止	2026-07-29 05:10:39.280637	2026-07-29 05:10:45.514689	8
58	1	1	帰り	完了	2026-07-29 05:10:47.751205	2026-07-29 05:12:36.730338	8
53	2	2	帰り	完了	2026-07-29 04:10:52.994089	2026-08-03 01:55:13.69252	8
41	2	2	帰り	完了	2026-07-27 22:53:42.296092	2026-08-03 23:29:24.963582	8
\.


--
-- Data for Name: children; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.children (id, name, class_name, qr_token, organization_id) FROM stdin;
1	さくら ちゃん	年少	child-sakura	8
2	はると くん	年長	child-haruto	8
3	つきくん	2号車ー先出し	a	8
\.


--
-- Data for Name: guardian_contacts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.guardian_contacts (id, organization_id, name, email, email_normalized, email_enabled, line_enabled, line_status, consented_at, consented_by, is_active, created_at, updated_at) FROM stdin;
2	8	さくらママ	tsuki2.springmoon@gmail.com	tsuki2.springmoon@gmail.com	t	t	pending	2026-07-28 07:27:57.613643	3	t	2026-07-28 07:27:57.614908	2026-07-28 07:28:36.705471
1	8	ママ	kazunyon@gmail.com	kazunyon@gmail.com	t	t	linked	2026-07-27 08:40:02.614266	3	t	2026-07-27 08:40:02.615232	2026-07-28 20:46:01.195478
\.


--
-- Data for Name: child_guardians; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.child_guardians (id, organization_id, child_id, guardian_contact_id, relationship, notify_alighted, created_at, updated_at) FROM stdin;
2	8	1	2	母	t	2026-07-28 07:27:57.683797	2026-07-28 07:27:57.683802
3	8	3	1	ままママ	t	2026-07-28 20:46:01.198706	2026-07-28 20:46:01.198709
4	8	1	1	ままママ	t	2026-07-28 20:46:01.198711	2026-07-28 20:46:01.198712
\.


--
-- Data for Name: line_contacts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.line_contacts (id, organization_id, line_user_id, display_name, is_active, created_at, updated_at, guardian_contact_id, last_webhook_event_id, last_event_at) FROM stdin;
3	8	U413f671378b5c4894c821654c4f7ee3d	\N	t	2026-07-27 21:04:30.470487	2026-07-28 07:29:29.097581	1	01KYKT1TP33PPC6TQYH3QP0Y1F	2026-07-28 07:29:28.918623
\.


--
-- Data for Name: notification_queue; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.notification_queue (id, recipient_type, recipient, message, status, created_at, organization_id, channel, provider_response, sent_at, guardian_contact_id, child_id, event_key, template_key, subject, attempt_count, next_attempt_at, provider_message_id, error_code) FROM stdin;
1	guardian	kazunyon@gmail.com	バナナ幼稚園のLINE通知連携案内を送信しました。期限は24時間です。	failed	2026-07-27 08:41:00.836033	8	email	EMAIL_WEBHOOK_URL が未設定です	\N	1	\N	line-link:1	line.link.v1	【まもるバス】バナナ幼稚園のLINE通知連携をお願いします	1	2026-07-27 08:42:00.838981	\N	configuration
2	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/27 17:59に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	queued	2026-07-27 08:59:20.602201	8	email	\N	\N	1	3	org:8:trip:33:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	0	\N	\N	\N
3	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/27 18:33に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	queued	2026-07-27 09:33:15.6392	8	email	\N	\N	1	3	org:8:trip:34:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	0	\N	\N	\N
4	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/27 18:41に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	queued	2026-07-27 09:41:05.119226	8	email	\N	\N	1	3	org:8:trip:35:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	0	\N	\N	\N
5	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/27 18:54に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	queued	2026-07-27 09:54:04.567586	8	email	\N	\N	1	3	org:8:trip:36:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	0	\N	\N	\N
6	guardian	kazunyon@gmail.com	バナナ幼稚園のLINE通知連携案内を送信しました。期限は24時間です。	failed	2026-07-27 09:57:03.114574	8	email	EMAIL_WEBHOOK_URL が未設定です	\N	1	\N	line-link:2	line.link.v1	【まもるバス】バナナ幼稚園のLINE通知連携をお願いします	1	2026-07-27 09:58:03.116644	\N	configuration
7	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/27 18:59に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	queued	2026-07-27 09:59:49.083594	8	email	\N	\N	1	3	org:8:trip:37:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	0	\N	\N	\N
8	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/27 19:24に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	queued	2026-07-27 10:24:11.077565	8	email	\N	\N	1	3	org:8:trip:38:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	0	\N	\N	\N
9	guardian	kazunyon@gmail.com	バナナ幼稚園のLINE通知連携案内を送信しました。期限は24時間です。	failed	2026-07-27 10:27:42.482818	8	email	EMAIL_WEBHOOK_URL が未設定です	\N	1	\N	line-link:3	line.link.v1	【まもるバス】バナナ幼稚園のLINE通知連携をお願いします	1	2026-07-27 10:28:42.555311	\N	configuration
10	guardian	kazunyon@gmail.com	バナナ幼稚園のLINE通知連携案内を送信しました。期限は24時間です。	failed	2026-07-27 10:45:40.692103	8	email	EMAIL_WEBHOOK_URL が未設定です	\N	1	\N	line-link:4	line.link.v1	【まもるバス】バナナ幼稚園のLINE通知連携をお願いします	1	2026-07-27 10:46:40.694582	\N	configuration
11	guardian	kazunyon@gmail.com	バナナ幼稚園のLINE通知連携案内を送信しました。期限は24時間です。	failed	2026-07-27 10:50:17.138881	8	email	EMAIL_WEBHOOK_URL が未設定です	\N	1	\N	line-link:5	line.link.v1	【まもるバス】バナナ幼稚園のLINE通知連携をお願いします	1	2026-07-27 10:51:17.19196	\N	configuration
12	guardian	kazunyon@gmail.com	バナナ幼稚園のLINE通知連携案内を送信しました。期限は24時間です。	failed	2026-07-27 20:05:39.716885	8	email	EMAIL_WEBHOOK_URL が未設定です	\N	1	\N	line-link:6	line.link.v1	【まもるバス】バナナ幼稚園のLINE通知連携をお願いします	1	2026-07-27 20:06:39.718881	\N	configuration
13	guardian	kazunyon@gmail.com	バナナ幼稚園のLINE通知連携案内を送信しました。期限は24時間です。	failed	2026-07-27 20:30:00.01255	8	email	EMAIL_WEBHOOK_URL が未設定です	\N	1	\N	line-link:7	line.link.v1	【まもるバス】バナナ幼稚園のLINE通知連携をお願いします	1	2026-07-27 20:31:00.014538	\N	configuration
14	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/28 06:06に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	queued	2026-07-27 21:06:26.329896	8	email	\N	\N	1	3	org:8:trip:40:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	0	\N	\N	\N
15	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/28 06:06に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	queued	2026-07-27 21:06:26.335737	8	line	\N	\N	1	3	org:8:trip:40:child:3:alighted	child.alighted.v1	\N	0	\N	\N	\N
17	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/28 07:54に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-27 22:54:09.174999	8	line	LINE HTTP 200	2026-07-27 22:54:09.397631	1	3	org:8:trip:41:child:3:alighted	child.alighted.v1	\N	1	\N	\N	\N
16	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/28 07:54に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-27 22:54:08.590744	8	email	HTTP 200	2026-07-27 23:20:27.128885	1	3	org:8:trip:41:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	4	\N	1f50fdff-81ee-4f15-9900-8702ccbaddff	\N
18	guardian	tsuki2.springmoon@gmail.com	バナナ幼稚園のLINE通知連携案内を送信しました。期限は24時間です。	sent	2026-07-28 07:28:36.696833	8	email	HTTP 200	2026-07-28 07:28:38.427073	2	\N	line-link:8	line.link.v1	【まもるバス】バナナ幼稚園のLINE通知連携をお願いします	1	\N	68397ad4-9937-4cc0-a8b4-c76e8fd8d38c	\N
19	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 07:57に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-28 22:57:06.093124	8	email	HTTP 200	2026-07-28 22:57:08.557308	1	3	org:8:trip:43:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	2c0298c5-f383-46c3-a088-57147bcb900b	\N
20	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 07:57に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-28 22:57:08.562446	8	line	LINE HTTP 200	2026-07-28 22:57:08.768803	1	3	org:8:trip:43:child:3:alighted	child.alighted.v1	\N	1	\N	\N	\N
21	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 09:04に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 00:04:37.893966	8	email	HTTP 200	2026-07-29 00:04:39.628211	1	3	org:8:trip:42:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	dc98c5e0-c321-45e4-bc28-db0876797845	\N
22	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 09:04に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 00:04:39.63274	8	line	LINE HTTP 200	2026-07-29 00:04:39.826636	1	3	org:8:trip:42:child:3:alighted	child.alighted.v1	\N	1	\N	\N	\N
23	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。さくら ちゃんさんの降車記録を2026/07/29 11:15に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 02:15:23.947949	8	email	HTTP 200	2026-07-29 02:15:25.754328	1	1	org:8:trip:44:child:1:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	ef961199-4a7a-4801-8e68-9132002756b7	\N
24	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。さくら ちゃんさんの降車記録を2026/07/29 11:15に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 02:15:25.758802	8	line	LINE HTTP 200	2026-07-29 02:15:25.979961	1	1	org:8:trip:44:child:1:alighted	child.alighted.v1	\N	1	\N	\N	\N
25	guardian	tsuki2.springmoon@gmail.com	まもるバスからのお知らせです。さくら ちゃんさんの降車記録を2026/07/29 11:15に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 02:15:25.983932	8	email	HTTP 200	2026-07-29 02:15:27.262986	2	1	org:8:trip:44:child:1:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	57617624-588b-47bf-a03f-167f0075a642	\N
26	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 11:42に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 02:42:58.703379	8	email	HTTP 200	2026-07-29 02:43:00.477574	1	3	org:8:trip:46:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	f3b2882d-addf-4c2c-879e-1d739fbfb684	\N
27	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 11:42に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 02:43:00.481828	8	line	LINE HTTP 200	2026-07-29 02:43:00.681168	1	3	org:8:trip:46:child:3:alighted	child.alighted.v1	\N	1	\N	\N	\N
28	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 12:39に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 03:39:31.018964	8	email	HTTP 200	2026-07-29 03:39:33.054475	1	3	org:8:trip:47:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	37a62f3c-54bd-432d-9aa5-99a52218818f	\N
29	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 12:39に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 03:39:33.059009	8	line	LINE HTTP 200	2026-07-29 03:39:33.244186	1	3	org:8:trip:47:child:3:alighted	child.alighted.v1	\N	1	\N	\N	\N
30	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 12:55に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 03:55:52.22479	8	email	HTTP 200	2026-07-29 03:55:53.847737	1	3	org:8:trip:48:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	bacb148c-4063-4503-acd9-183e46e24cdd	\N
31	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 12:55に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 03:55:53.852128	8	line	LINE HTTP 200	2026-07-29 03:55:54.079575	1	3	org:8:trip:48:child:3:alighted	child.alighted.v1	\N	1	\N	\N	\N
32	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 13:08に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 04:08:21.908816	8	email	HTTP 200	2026-07-29 04:08:23.370034	1	3	org:8:trip:51:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	9260bac4-d5dc-495b-bf64-af4ec1b45f7f	\N
33	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 13:08に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 04:08:23.374014	8	line	LINE HTTP 200	2026-07-29 04:08:23.587528	1	3	org:8:trip:51:child:3:alighted	child.alighted.v1	\N	1	\N	\N	\N
34	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 13:09に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 04:09:32.750998	8	email	HTTP 200	2026-07-29 04:09:34.059446	1	3	org:8:trip:52:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	040a352f-b83d-4b48-9b82-5bef87af7c90	\N
35	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 13:09に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 04:09:34.063072	8	line	LINE HTTP 200	2026-07-29 04:09:34.418939	1	3	org:8:trip:52:child:3:alighted	child.alighted.v1	\N	1	\N	\N	\N
36	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 13:44に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 04:44:02.071158	8	email	HTTP 200	2026-07-29 04:44:08.072989	1	3	org:8:trip:53:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	b92321c2-4840-4d83-b20e-4cd75af94603	\N
37	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 13:44に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 04:44:08.077193	8	line	LINE HTTP 200	2026-07-29 04:44:08.292528	1	3	org:8:trip:53:child:3:alighted	child.alighted.v1	\N	1	\N	\N	\N
38	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 13:45に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 04:45:28.67651	8	email	HTTP 200	2026-07-29 04:45:30.211993	1	3	org:8:trip:54:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	d911e26c-d6e0-4814-8915-b599f022f721	\N
39	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 13:45に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 04:45:30.219774	8	line	LINE HTTP 200	2026-07-29 04:45:30.404327	1	3	org:8:trip:54:child:3:alighted	child.alighted.v1	\N	1	\N	\N	\N
40	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 13:46に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 04:46:45.317364	8	email	HTTP 200	2026-07-29 04:46:46.738171	1	3	org:8:trip:55:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	e6e32d77-2e9c-4b4e-9c13-0e58fc0aa7cb	\N
41	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 13:46に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 04:46:46.743183	8	line	LINE HTTP 200	2026-07-29 04:46:46.953981	1	3	org:8:trip:55:child:3:alighted	child.alighted.v1	\N	1	\N	\N	\N
42	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 14:04に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 05:04:03.583558	8	email	HTTP 200	2026-07-29 05:04:05.113094	1	3	org:8:trip:56:child:3:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	8cd8ae1d-fc51-4a09-a03a-913c549cf45a	\N
43	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。つきくんさんの降車記録を2026/07/29 14:04に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 05:04:05.117382	8	line	LINE HTTP 200	2026-07-29 05:04:05.335991	1	3	org:8:trip:56:child:3:alighted	child.alighted.v1	\N	1	\N	\N	\N
44	guardian	kazunyon@gmail.com	まもるバスからのお知らせです。さくら ちゃんさんの降車記録を2026/07/29 14:11に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 05:11:15.480475	8	email	HTTP 200	2026-07-29 05:11:17.310798	1	1	org:8:trip:58:child:1:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	861da4ab-7dae-4a2c-922d-ac0d7ea8218e	\N
45	guardian	U413f671378b5c4894c821654c4f7ee3d	まもるバスからのお知らせです。さくら ちゃんさんの降車記録を2026/07/29 14:11に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 05:11:17.31461	8	line	LINE HTTP 200	2026-07-29 05:11:17.699987	1	1	org:8:trip:58:child:1:alighted	child.alighted.v1	\N	1	\N	\N	\N
46	guardian	tsuki2.springmoon@gmail.com	まもるバスからのお知らせです。さくら ちゃんさんの降車記録を2026/07/29 14:11に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。	sent	2026-07-29 05:11:17.703836	8	email	HTTP 200	2026-07-29 05:11:19.113166	2	1	org:8:trip:58:child:1:alighted	child.alighted.v1	【まもるバス】降車記録のお知らせ	1	\N	6d7c6021-8b77-4e43-9d59-74148488d986	\N
\.


--
-- Data for Name: line_link_requests; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.line_link_requests (id, organization_id, guardian_contact_id, token_hash, status, expires_at, requested_by, email_notification_id, used_at, created_at) FROM stdin;
1	8	1	4f849418a06173ae5732e07345bdfe1e849fbd0f08cb90490a4b0a63b7699bfa	revoked	2026-07-28 08:40:59.815022	3	1	\N	2026-07-27 08:40:59.816146
2	8	1	733562a9f3954500873f6d3329003c50408e87166781b53e1fb0540f588bbcf5	revoked	2026-07-28 09:57:02.723077	3	6	\N	2026-07-27 09:57:02.724345
3	8	1	f89178b111d02010b1c81cfa601d803e608041b1bbe8744e6b3934bbf8a497f8	revoked	2026-07-28 10:27:42.210846	3	9	\N	2026-07-27 10:27:42.211882
4	8	1	ff2d013aa293734306b01c45187c41d21691717240c27b30218516ed11a14e06	revoked	2026-07-28 10:45:40.274574	3	10	\N	2026-07-27 10:45:40.275957
5	8	1	c5a8f212366d78f2a53c3e8c5ab3915523c73d094f99703c9a4b631dcbfb65b9	revoked	2026-07-28 10:50:17.127067	3	11	\N	2026-07-27 10:50:17.127353
6	8	1	7e36f6bb62dae7d1846d081a1948a55208006ff122ec234f99513aa1f063fcf2	revoked	2026-07-28 20:05:39.379068	3	12	\N	2026-07-27 20:05:39.380225
7	8	1	a6bbb0718dec4fab4ca80430952a5ca4863877d141fc550ebccc5a1fed05f49f	used	2026-07-28 20:29:59.944813	3	13	2026-07-27 21:04:30.475175	2026-07-27 20:29:59.945898
8	8	2	eb024f2e3009768e60b5e67b1cb5c742f9880c5001a174c87f011afa5755a3e7	pending	2026-07-29 07:28:35.729569	3	18	\N	2026-07-28 07:28:35.730487
\.


--
-- Data for Name: route_children; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.route_children (id, route_id, child_id) FROM stdin;
1	1	1
2	1	2
11	3	1
12	3	2
15	4	3
16	2	3
\.


--
-- Data for Name: safety_events; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.safety_events (id, child_id, event_type, staff_name, latitude, longitude, created_at) FROM stdin;
\.


--
-- Data for Name: sync_events; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sync_events (id, organization_id, client_event_id, outcome, created_at) FROM stdin;
\.


--
-- Data for Name: trip_attendance; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.trip_attendance (id, trip_id, child_id, boarded_at, alighted_at, boarded_by, alighted_by) FROM stdin;
1	1	1	2026-07-23 21:00:45.251849	2026-07-23 21:01:48.191342	田中 先生	田中 先生
2	1	2	2026-07-23 21:01:11.931889	2026-07-23 21:02:03.394331	田中 先生	田中 先生
3	7	1	2026-07-24 19:40:18.08413	2026-07-24 20:38:38.321706	通常名簿	管理者（QRなし）
4	7	2	2026-07-24 19:40:18.08413	2026-07-24 20:38:47.858682	通常名簿	管理者（QRなし）
5	8	1	2026-07-24 21:16:40.854628	\N	通常名簿	\N
6	8	2	2026-07-24 21:16:40.854628	\N	通常名簿	\N
7	9	1	2026-07-24 22:51:04.962824	\N	通常名簿	\N
8	9	2	2026-07-24 22:51:04.962824	\N	通常名簿	\N
9	10	1	2026-07-24 22:52:40.303082	2026-07-24 22:52:51.805894	通常名簿	管理者（QRなし）
10	10	2	2026-07-24 22:52:40.303082	2026-07-24 22:53:00.836048	通常名簿	管理者（QRなし）
11	11	1	2026-07-24 23:02:49.390272	\N	通常名簿	\N
12	11	2	2026-07-24 23:02:49.390272	\N	通常名簿	\N
13	12	1	2026-07-24 23:03:00.68565	\N	通常名簿	\N
14	12	2	2026-07-24 23:03:00.68565	\N	通常名簿	\N
15	13	1	2026-07-24 23:30:13.882922	\N	通常名簿	\N
16	13	2	2026-07-24 23:30:13.882922	\N	通常名簿	\N
17	14	1	2026-07-25 01:30:02.933239	\N	通常名簿	\N
18	14	2	2026-07-25 01:30:02.933239	\N	通常名簿	\N
19	15	1	2026-07-25 01:33:24.269847	\N	通常名簿	\N
20	15	2	2026-07-25 01:33:24.269847	\N	通常名簿	\N
21	16	1	2026-07-25 01:36:02.568694	\N	通常名簿	\N
22	16	2	2026-07-25 01:36:02.568694	\N	通常名簿	\N
64	52	3	2026-07-29 04:09:03.250727	2026-07-29 04:09:32.743643	通常名簿	管理者（QRなし）
23	18	1	2026-07-25 06:32:57.055132	2026-07-25 08:25:47.108516	管理者（QRなし）	管理者（QRなし）
24	18	2	2026-07-25 06:33:06.37482	2026-07-25 08:25:52.068893	管理者（QRなし）	管理者（QRなし）
25	19	1	\N	\N	\N	\N
26	19	2	\N	\N	\N	\N
27	20	3	2026-07-25 22:46:23.410008	2026-07-25 22:46:47.619933	管理者（QRなし）	管理者（QRなし）
65	53	3	2026-07-29 04:10:52.994089	2026-07-29 04:44:01.984493	通常名簿	管理者（QRなし）
29	22	3	2026-07-25 22:56:33.71642	2026-07-25 23:06:03.750738	管理者	管理者
28	21	3	2026-07-25 23:28:46.144832	2026-07-25 23:28:52.781687	管理者	管理者
30	23	1	\N	\N	\N	\N
31	23	2	\N	\N	\N	\N
32	24	3	2026-07-25 23:55:38.616487	2026-07-26 01:23:18.244731	通常名簿	管理者
33	25	1	\N	\N	\N	\N
34	25	2	\N	\N	\N	\N
35	26	3	2026-07-26 02:22:03.278992	2026-07-26 02:22:39.498154	通常名簿	管理者（QRなし）
36	27	3	2026-07-26 03:56:16.920642	2026-07-26 03:56:32.311113	通常名簿	管理者（QRなし）
37	28	3	2026-07-26 04:36:11.162842	2026-07-26 04:36:27.274349	通常名簿	管理者（QRなし）
38	29	3	2026-07-26 07:28:48.542341	\N	通常名簿	\N
39	30	1	2026-07-26 07:29:20.677885	\N	通常名簿	\N
40	30	2	2026-07-26 07:29:20.677885	\N	通常名簿	\N
41	31	3	2026-07-27 02:34:38.296474	\N	通常名簿	\N
42	32	3	2026-07-27 02:36:25.199597	2026-07-27 08:26:48.797384	通常名簿	管理者（QRなし）
43	33	3	2026-07-27 08:58:41.375998	2026-07-27 08:59:20.595932	通常名簿	管理者
44	34	3	2026-07-27 09:32:37.173789	2026-07-27 09:33:15.630947	通常名簿	管理者
45	35	3	2026-07-27 09:40:53.156937	2026-07-27 09:41:05.113613	通常名簿	管理者
46	36	3	2026-07-27 09:53:51.256467	2026-07-27 09:54:04.559503	通常名簿	管理者
47	37	3	2026-07-27 09:59:39.114	2026-07-27 09:59:49.077452	通常名簿	管理者
48	38	3	2026-07-27 10:23:53.954896	2026-07-27 10:24:11.037393	通常名簿	管理者
49	39	3	2026-07-27 10:49:40.652487	\N	通常名簿	\N
50	40	3	2026-07-27 20:05:13.417054	2026-07-27 21:06:26.320188	通常名簿	管理者
51	41	3	2026-07-27 22:53:42.296092	2026-07-27 22:54:08.577504	通常名簿	管理者
53	43	3	2026-07-28 22:55:45.473118	2026-07-28 22:57:06.082357	通常名簿	管理者
52	42	3	2026-07-28 07:33:49.965651	2026-07-29 00:04:37.826224	通常名簿	管理者
66	54	3	2026-07-29 04:45:14.561203	2026-07-29 04:45:28.669647	通常名簿	管理者（QRなし）
54	44	1	2026-07-29 00:06:21.576439	2026-07-29 02:15:23.928564	管理者	管理者（QRなし）
55	44	2	2026-07-29 02:14:28.844672	2026-07-29 02:15:52.246863	管理者（QRなし）	管理者（QRなし）
56	45	1	\N	\N	\N	\N
57	45	2	\N	\N	\N	\N
58	46	3	2026-07-29 02:42:39.249413	2026-07-29 02:42:58.690711	通常名簿	管理者（QRなし）
59	47	3	2026-07-29 03:38:58.073646	2026-07-29 03:39:31.005068	通常名簿	管理者
60	48	3	2026-07-29 03:39:55.89882	2026-07-29 03:55:52.033058	通常名簿	管理者
61	49	3	2026-07-29 03:56:27.744933	\N	通常名簿	\N
62	50	3	2026-07-29 03:57:32.124215	\N	通常名簿	\N
63	51	3	2026-07-29 04:08:08.468809	2026-07-29 04:08:21.900928	通常名簿	管理者（QRなし）
67	55	3	2026-07-29 04:46:00.156358	2026-07-29 04:46:45.31147	通常名簿	管理者（QRなし）
68	56	3	2026-07-29 05:03:06.271239	2026-07-29 05:04:03.575049	通常名簿	管理者（QRなし）
69	57	3	\N	\N	\N	\N
70	58	1	2026-07-29 05:10:47.751205	2026-07-29 05:11:15.474232	通常名簿	管理者
71	58	2	2026-07-29 05:10:47.751205	2026-07-29 05:11:35.622741	通常名簿	管理者（QRなし）
\.


--
-- Data for Name: vehicle_safety_checks; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.vehicle_safety_checks (id, check_type, staff_id, staff_name, qr_token, latitude, longitude, created_at, organization_id, trip_id) FROM stdin;
1	tail_qr	3	管理者	bus-tail-2	35.940486	139.648803	2026-07-24 20:39:38.973731	8	7
2	third_party	2	佐藤 先生	third-party-confirmed	\N	\N	2026-07-24 21:13:36.306374	8	7
3	tail_qr	3	管理者	bus-tail-2	35.940486	139.648803	2026-07-24 22:53:29.968203	8	10
4	third_party	2	佐藤 先生	third-party-confirmed	\N	\N	2026-07-24 22:54:55.634853	8	10
5	tail_qr	3	管理者	bus-tail-2	35.94076202965952	139.64867316170225	2026-07-25 08:26:48.454998	8	18
6	third_party	2	佐藤 先生	third-party-confirmed	\N	\N	2026-07-25 08:27:23.333071	8	18
7	tail_qr	3	管理者	bus-tail-2	35.9404865	139.6488045	2026-07-25 22:47:21.727855	8	20
8	third_party	2	佐藤 先生	third-party-confirmed	\N	\N	2026-07-25 22:47:35.913523	8	20
9	tail_qr	3	管理者	bus-tail-2	35.94075537525822	139.64866019998377	2026-07-25 23:26:58.871906	8	22
10	third_party	2	佐藤 先生	third-party-confirmed	\N	\N	2026-07-25 23:27:28.60697	8	22
11	tail_qr	3	管理者	bus-tail-2	35.94077197480669	139.64870245451152	2026-07-25 23:29:38.349112	8	21
12	third_party	2	佐藤 先生	third-party-confirmed	\N	\N	2026-07-25 23:29:57.806427	8	21
13	tail_qr	3	管理者	bus-tail-2	35.9404865	139.6488045	2026-07-26 01:23:43.628309	8	24
14	tail_qr	3	管理者	bus-tail-2	35.9404865	139.6488045	2026-07-26 01:23:43.72738	8	24
15	third_party	2	佐藤 先生	third-party-confirmed	\N	\N	2026-07-26 01:24:05.530688	8	24
16	tail_qr	3	管理者	bus-tail-2	35.94075886289504	139.6486626807406	2026-07-26 02:23:17.408508	8	26
17	tail_qr	3	管理者	bus-tail-2	35.940758980796	139.64866268542207	2026-07-26 02:23:17.481812	8	26
18	third_party	2	佐藤 先生	third-party-confirmed	\N	\N	2026-07-26 03:33:56.600598	8	26
19	tail_qr	3	管理者	bus-tail-2	35.9404865	139.6488045	2026-07-26 03:56:58.813729	8	27
20	tail_qr	3	管理者	bus-tail-2	35.9404865	139.6488045	2026-07-26 03:56:58.814423	8	27
21	third_party	2	佐藤 先生	third-party-confirmed	\N	\N	2026-07-26 04:11:02.503584	8	27
22	tail_qr	3	管理者	bus-tail-2	35.940487	139.648806	2026-07-26 04:36:45.238521	8	28
23	tail_qr	3	管理者	bus-tail-2	35.940487	139.648806	2026-07-26 04:36:45.241508	8	28
24	third_party	2	佐藤 先生	third-party-confirmed	\N	\N	2026-07-26 04:37:18.616207	8	28
25	tail_qr	3	管理者	bus-tail-2	35.94079035943579	139.648653549125	2026-07-28 23:04:54.662583	8	43
26	third_party	2	佐藤 先生	third-party-confirmed	\N	\N	2026-07-28 23:06:00.433461	8	43
27	tail_qr	3	管理者	bus-tail-2	35.94076913368163	139.64866638304932	2026-07-29 00:05:06.637883	8	42
28	tail_qr	3	管理者	bus-tail-2	35.94076913368163	139.64866638304932	2026-07-29 00:05:06.638386	8	42
29	third_party	2	佐藤 先生	third-party-confirmed	\N	\N	2026-07-29 00:05:51.725261	8	42
30	tail_qr	3	管理者	bus-tail-2	35.94076909913952	139.64866552577288	2026-07-29 02:18:55.105302	8	44
31	third_party	2	佐藤 先生	third-party-confirmed	\N	\N	2026-07-29 02:42:14.664534	8	44
32	tail_qr	3	管理者	return-vehicle-check	35.9407689415013	139.6486654991816	2026-07-29 02:43:05.249558	8	46
33	tail_qr	3	管理者	return-vehicle-check	35.94076871705108	139.64866542217405	2026-07-29 03:39:53.113019	8	47
34	tail_qr	3	管理者	return-vehicle-check	35.940771801580745	139.64870709908348	2026-07-29 03:56:16.266235	8	48
35	tail_qr	3	管理者	return-vehicle-check	35.940768778541575	139.6486654322165	2026-07-29 04:08:57.245984	8	51
36	tail_qr	3	管理者	return-vehicle-check	35.94076885452623	139.64866543097926	2026-07-29 04:10:43.596994	8	52
37	tail_qr	3	管理者	return-vehicle-check	35.94077189664428	139.6486669207927	2026-07-29 04:45:54.707758	8	54
38	tail_qr	3	管理者	return-vehicle-check	35.940769807232336	139.64866538814593	2026-07-29 05:02:53.962838	8	55
39	tail_qr	3	管理者	return-vehicle-check	35.94076970655706	139.64866539088095	2026-07-29 05:04:45.37451	8	56
40	tail_qr	3	管理者	return-vehicle-check	35.94076941177276	139.64866526255915	2026-07-29 05:12:36.225691	8	58
41	tail_qr	3	管理者	return-vehicle-check	35.92782875890047	139.63014009694518	2026-08-03 01:55:13.543023	8	53
42	tail_qr	3	管理者	return-vehicle-check	35.9404865	139.6488045	2026-08-03 23:29:24.518889	8	41
\.


--
-- Data for Name: video_evidence; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.video_evidence (id, organization_id, trip_id, uploaded_by, file_name, storage_key, content_type, ai_status, ai_result, created_at) FROM stdin;
1	8	26	3	vehicle-check-26-2026-07-26T03-33-10-566Z.webm	8/f774d114-bcde-4e67-804b-5263bce78f25.webm	video/webm;codecs=vp9	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-07-26 03:33:28.37383
2	8	27	3	vehicle-check-27-2026-07-26T04-10-10-419Z.mp4	8/5b5f738d-8df9-4340-ac0f-7a55d1636aef.mp4	video/mp4;codecs=avc1	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-07-26 04:10:12.960391
3	8	28	3	vehicle-check-28-2026-07-26T04-37-02-144Z.mp4	8/c8c0204c-c2cc-4d50-9d98-65fa300212c9.mp4	video/mp4;codecs=avc1	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-07-26 04:37:05.817286
4	8	43	3	vehicle-check-43-2026-07-28T23-05-17-979Z.mp4	8/e5150cbb-efcf-4c01-9227-bfbaacb49b26.mp4	video/mp4; codecs=avc1.42000a	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-07-28 23:05:29.290122
5	8	42	3	vehicle-check-42-2026-07-29T00-05-26-697Z.mp4	8/bd6c5a2b-8275-47a9-b70c-667ef9c45c72.mp4	video/mp4; codecs=avc1.42000a	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-07-29 00:05:30.489348
6	8	48	3	vehicle-check-48-2026-07-29T03-56-14-454Z.mp4	8/103a1f69-dee1-4839-96dc-1c18d15b5b56.mp4	video/mp4; codecs=avc1.42000a	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-07-29 03:56:15.787024
7	8	51	3	vehicle-check-51-2026-07-29T04-08-54-525Z.mp4	8/d6031081-2dc0-4a93-b43e-827d7b30f50a.mp4	video/mp4; codecs=avc1.42000a	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-07-29 04:08:56.870104
8	8	52	3	vehicle-check-52-2026-07-29T04-10-41-847Z.mp4	8/25206ae0-3fd7-4e0a-a960-29a96ae014e3.mp4	video/mp4; codecs=avc1.42000a	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-07-29 04:10:43.192919
9	8	53	3	vehicle-check-53-2026-07-29T04-44-26-112Z.mp4	8/0e1bc0c7-68e8-450b-90d9-16c19abe03c8.mp4	video/mp4; codecs=avc1.42000a	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-07-29 04:44:31.103521
10	8	54	3	vehicle-check-54-2026-07-29T04-45-47-261Z.mp4	8/f41acf27-0f9a-46db-a6ee-a1df480a1018.mp4	video/mp4; codecs=avc1.42000a	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-07-29 04:45:50.862286
11	8	55	3	vehicle-check-55-2026-07-29T04-47-20-742Z.mp4	8/2a93ec22-bfce-498a-ac27-026fc5255877.mp4	video/mp4; codecs=avc1.42000a	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-07-29 04:47:23.023122
12	8	56	3	vehicle-check-56-2026-07-29T05-04-25-278Z.mp4	8/78d1c055-e79e-425b-a758-68749b252b73.mp4	video/mp4; codecs=avc1.42000a	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-07-29 05:04:28.817321
13	8	58	3	vehicle-check-58-2026-07-29T05-12-32-881Z.mp4	8/54ef0fef-fcef-4d25-92ae-6a0cbde3dd78.mp4	video/mp4; codecs=avc1.42000a	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-07-29 05:12:35.393611
14	8	53	3	vehicle-check-53-2026-08-03T01-55-06-951Z.mp4	8/5f80e7fd-db32-4984-b361-9c878a6b5bd1.mp4	video/mp4; codecs=avc1.42000a	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-08-03 01:55:09.63903
15	8	41	3	vehicle-check-41-2026-08-03T23-29-14-679Z.mp4	8/930d54bd-eaac-4333-9eda-47748a0c8b0d.mp4	video/mp4;codecs=avc1	needs_human_review	AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください	2026-08-03 23:29:15.399358
\.


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 368, true);


--
-- Name: bus_routes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.bus_routes_id_seq', 4, true);


--
-- Name: bus_trips_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.bus_trips_id_seq', 58, true);


--
-- Name: child_guardians_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.child_guardians_id_seq', 4, true);


--
-- Name: children_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.children_id_seq', 3, true);


--
-- Name: guardian_contacts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.guardian_contacts_id_seq', 2, true);


--
-- Name: line_contacts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.line_contacts_id_seq', 3, true);


--
-- Name: line_link_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.line_link_requests_id_seq', 8, true);


--
-- Name: notification_queue_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.notification_queue_id_seq', 46, true);


--
-- Name: organizations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.organizations_id_seq', 8, true);


--
-- Name: route_children_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.route_children_id_seq', 16, true);


--
-- Name: safety_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.safety_events_id_seq', 1, false);


--
-- Name: staff_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.staff_id_seq', 2, true);


--
-- Name: sync_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sync_events_id_seq', 1, false);


--
-- Name: trip_attendance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.trip_attendance_id_seq', 71, true);


--
-- Name: vehicle_safety_checks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.vehicle_safety_checks_id_seq', 42, true);


--
-- Name: vehicles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.vehicles_id_seq', 8, true);


--
-- Name: video_evidence_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.video_evidence_id_seq', 15, true);


--
-- PostgreSQL database dump complete
--

\unrestrict PT4bwAZNNX18ltxXCNSMwikdxQM9pe96EhCgtZtbAF7ydlsG7RNq4a79gHaj621

