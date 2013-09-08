drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  switch_name text not null,
  switch_channel integer not null,
  switch_button integer not null,
  switch_last_state text
);


