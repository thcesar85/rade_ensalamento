CREATE TABLE "execucao" (
  "id" integer PRIMARY KEY,
  "data_execucao" timestamp
);

CREATE TABLE "lobby_ensalamento" (
  "id" integer PRIMARY KEY,
  "entityCode" integer,
  "courseCode" integer,
  "groupCode" integer,
  "place" varcahr(50),
  "taskCode" integer,
  "lobby_date" date,
  "startTime" varchar(10),
  "endTime" varchar(10),
  "studant" varchar(20),
  "id_execucao" integer
);

CREATE TABLE "log_enturmacao" (
  "id" integer PRIMARY KEY,
  "id_execucao" integer,
  "id_lobby_ensalamento" integer,
  "studant" varchar(20),
  "response" varchar(max)
);

ALTER TABLE "lobby_ensalamento" ADD FOREIGN KEY ("id_execucao") REFERENCES "execucao" ("id");

ALTER TABLE "log_enturmacao" ADD FOREIGN KEY ("id_lobby_ensalamento") REFERENCES "lobby_ensalamento" ("id");

ALTER TABLE "log_enturmacao" ADD FOREIGN KEY ("id_execucao") REFERENCES "execucao" ("id");

ALTER TABLE "log_enturmacao" ADD FOREIGN KEY ("id_execucao") REFERENCES "lobby_ensalamento" ("id_execucao");
