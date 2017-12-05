# coding=utf-8

@yui.admin
@yui.command('sql')
def sql(msg, user):
    """Execute an SQLite query. Usage: sql <query>"""
    split = msg.split(' ', 1)
    if len(split) < 2:
        return

    try:
        c = yui.db.cursor()
        c.execute(split[1])
        text = '%s rows affected' % c.rowcount
        rows = c.fetchall()
        yui.db.commit()
        if len(rows) > 0:
            text = ''
            for r in rows:
                text += str(r)
        return text
    except Exception as e:
        return str(e)
