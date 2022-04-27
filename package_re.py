import re

#search vs match, use Module Contents
match = re.match("c", "abcdef") #return Match Object, find match at start of string
if match:
    print(match.group(0)) #get all match
else:
    print('match is: ', match)

#so re.search() is more useful.
second_match = re.search("c", "abcdefc")
if second_match:
    print('the match is: ', second_match.group()) #find first match in all string
else:
    print('second_match is: ', second_match)

#re.findall() return list
#so re.search with Match.group(0) and re.findall() is more useful
all_match = re.findall(r'c', 'abcdefc')
if all_match:
    print('all_match: ', all_match)
else:
    print('all match is: ', all_match)

#with Match just need to know method group, start, end
email = "tony@tiremove_thisger.net"
m = re.search("remove_this", email)
print(email[m.start():m.end()])