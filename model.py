from config import Config
from elasticsearch import helpers
from pprint import pprint
import traceback
from wasl import Wasl
import time
config = Config()

def time_forward(str_t):
    return time.mktime(time.strptime(str_t, '%Y-%m-%d %H:%M:%S'))

def time_backward(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))

class Label:

    def __init__(self):
        pass

    def migrate(self):
        conn, cur = config.mysql_conn, config.mysql_cur
        cur.execute('''
            CREATE TABLE IF NOT EXISTS `labels` (
                id int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT,
                name nvarchar(1024),
                description nvarchar(1024),
                severity int(11),
                reference nvarchar(1024)
            )
        ''')
        conn.commit()

    def get(self):
        conn, cur = config.mysql_conn, config.mysql_cur
        cur.execute('SELECT * FROM `users`')
        return cur.fetchall()


class Alert:

    def __init__(self):
        pass

    def migrate(self):
        conn, cur = config.mysql_conn, config.mysql_cur
        cur.execute('''
            CREATE TABLE IF NOT EXISTS `alerts` (
                `id` int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT,
                `label_id` int(11),
                `victim_id` int(11),
                `type` nvarchar(1024),
                `false_positive` tinyint(1),
                `start_at` timestamp,
                `end_at` timestamp,
                `attacker` nvarchar(1024),
                `screenshot` nvarchar(1024),
                FOREIGN KEY (label_id) REFERENCES labels(id)
            )
        ''')
        conn.commit()

    def insert(self, alert):
        conn, cur = config.mysql_conn, config.mysql_cur
        cur.execute('SELECT id, attacker, end_at FROM alerts GROUP BY end_at DESC LIMIT 1')
        row = cur.fetchone()
        if row:
            id, attacker, end_at = row
            alert['attacker'] = ','.join(set(attacker.split(',')+alert['attacker'].split(',')))
            alert['id'] = id
            if time_forward(alert['end_at']) - time_forward(str(end_at)) < 3600:
                cur.execute('UPDATE alerts SET end_at=\'{end_at}\', attacker=\'{attacker}\' WHERE id=\'{id}\''.format(**alert)) 
            else:
                cur.execute('''INSERT INTO alerts (label_id, victim_id, type, false_positive, start_at, end_at, attacker) 
                    VALUES ({label_id}, {victim_id}, \'{type}\', {false_positive}, \'{start_at}\', \'{end_at}\', \'{attacker}\')'''.format(**alert)) 
        else:
            cur.execute('''INSERT INTO alerts (label_id, victim_id, type, false_positive, start_at, end_at, attacker) 
                VALUES ({label_id}, {victim_id}, \'{type}\', {false_positive}, \'{start_at}\', \'{end_at}\', \'{attacker}\')'''.format(**alert)) 
        conn.commit()

class Rule:

    def __init__(self):
        pass

    def migrate(self):
        conn, cur = config.mysql_conn, config.mysql_cur
        cur.execute('''
            CREATE TABLE IF NOT EXISTS `rules` (
                id int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT,
                label_id int(11),
                wasl_query nvarchar(1024),
                tag nvarchar(1024),
                FOREIGN KEY (label_id) REFERENCES labels(id)
            )
        ''')
        conn.commit()

    def get(self):
        conn, cur = config.mysql_conn, config.mysql_cur
        cur.execute('SELECT * FROM `rules`')
        return cur.fetchall()


class Agent:

    def __init__(self):
        pass

    def migrate(self):
        conn, cur = config.mysql_conn, config.mysql_cur
        cur.execute('''
            CREATE TABLE IF NOT EXISTS `agents` (
                id int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT,
                agent_name nvarchar(1024)
            )
        ''')
        conn.commit()

    def get(self):
        conn, cur = config.mysql_conn, config.mysql_cur
        cur.execute('SELECT id, agent_name FROM `agents`')
        return cur.fetchall()



class Log:

    def __init__(self):
        self.wasl = Wasl(config.es)

    def get(self, wasl_query):
        # pprint(self.wasl.wasl2elasticsearch(wasl_query))
        for item in self.wasl.scroll(wasl_query):
            print(item)

def reset_database():
    conn, cur = config.mysql_conn, config.mysql_cur
    cur.execute('DROP TABLE `alerts`')
    cur.execute('DROP TABLE `rules`')
    cur.execute('DROP TABLE `labels`')
    cur.execute('DROP TABLE `agents`')
    conn.commit()


if __name__ == '__main__':
    # reset_database()
    # Agent().migrate()
    Label().migrate()
    Alert().migrate()
    Rule().migrate()
    # pass
