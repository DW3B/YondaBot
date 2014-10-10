import praw, sqlite3, time, sys, re
from getpass import getpass

print '''
========== /r/Yonda Bot ==========
Version: 0.5
'''

#========== BOT CONFIGURATION ==========#
BOT_NAME	= ''				# Enter bot's name
PASSWORD	= getpass('Password: ')
USER_AGENT	= 'YondaBot auto-mod for /r/Yonda. Author: D_Web'
SUBREDDIT	= 'BotDevelopment'

#========== REPLIES/POST PARSING CONFIG ==========#
#TODO: Add some shit here...

#========== SQL DB CONFIGURATION ==========#
print '\nSetting up SQL Database...',
sql = sqlite3.connect('yondabot.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS oldcomments(ID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS users(NAME TEXT, STAT_POINTS INTEGER, REG_POINTS INTEGER, INVENTORY TEXT)')
sql.commit()
print 'DONE'

#========== REDDIT LOGIN / PRAW SETUP ==========#
print 'Logging into Reddit...',
r = praw.Reddit(USER_AGENT)
r.login(BOT_NAME, PASSWORD)
print 'DONE'

def UpdateFlair(user, sPoints, rPoints):
	allFlair = r.get_subreddit(SUBREDDIT).get_flair_list()
	for entry in allFlair:
		if entry['user'] == user:
			currentFlair = entry['flair_text']
	try:
		if currentFlair:
			charName = re.search('\[(.*?)\]', currentFlair).group(0)
			newFlair = '%s S+%i R+%i' % (charName, sPoints, rPoints)
	except:
		newFlair = 'S+%i R+%i' % (sPoints, rPoints)
	r.get_subreddit(SUBREDDIT).set_flair(user, newFlair)

def UpdatePoints(user, points):
	try:
		sPoints, rPoints = cur.execute('SELECT stat_points, reg_points FROM users WHERE name=?', (user,)).fetchone()
		newSpoints = sPoints + 1
		newRpoints = rPoints + points
		cur.execute('UPDATE users SET stat_points=?, reg_points=? WHERE name=?', (newSpoints, newRpoints, user))
		UpdateFlair(user, newSpoints, newRpoints)
	except:
		cur.execute('INSERT INTO users VALUES(?,?,?,?)', (user, 1, points, ''))
		UpdateFlair(user, 1, points)
	sql.commit()
		

def SubScan():
	sub = r.get_subreddit(SUBREDDIT)
	posts = sub.get_new(limit=100)
	for p in posts:
		pAuth = p.author.name
		cur.execute('SELECT * FROM oldposts WHERE id=?', (p.id,))
		if not cur.fetchone() and pAuth != '' and pAuth.lower() != BOT_NAME.lower():
			if p.is_self:
				wordCount = len(p.selftext.split())
			else:
				wordCount = 0
			print 'Post by %s is %i words long.' % (pAuth, wordCount)
			UpdatePoints(pAuth, wordCount)
			cur.execute('INSERT INTO oldposts VALUES(?)', (p.id,))
			sql.commit()
		for c in p.comments:
			cAuth = c.author.name
			cur.execute('SELECT * FROM oldcomments WHERE id=?', (c.id,))
			if not cur.fetchone() and cAuth != '':
				wordCount = len(c.body.split())
				print 'Comment by %s is %i words long.' % (cAuth, wordCount)
				UpdatePoints(cAuth, wordCount)
			cur.execute('INSERT INTO oldcomments VALUES(?)', (c.id,))
			sql.commit()

def CheckMessages():
	pass #TODO: Add some shit here

try:
	while True:
		SubScan()
except KeyboardInterrupt:
	print '\nGoodbye!'
	sys.exit()






