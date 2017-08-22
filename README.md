# BroadcastBot

A reddit bot that makes it possible for users
to broadcast messages to those who've subscribed.

## Setup

Setup the database like such:

```sql
CREATE TABLE subscribers(
	name char(20) not null,
	id char(10) not null,
	timestamp timestamp not null DEFAULT NOW()
);

CREATE FUNCTION clearExpired() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  DELETE FROM subscribers WHERE timestamp < NOW() - INTERVAL '7 days';
  RETURN NEW;
END;
$$;

CREATE TRIGGER clearExpiredTrigger
    AFTER INSERT ON subscribers
    EXECUTE PROCEDURE clearExpired();
```
