from __future__ import unicode_literals

from six import text_type

from database_sanitizer.session import hash_text_to_int, hash_text_to_ints


def sanitize_email(value):
    if not value:
        return value
    (num1, num2, num3) = hash_text_to_ints(value.strip(), [16, 16, 32])
    given_name = given_names[num1 % given_names_count]
    surname = surnames[num2 % surnames_count]
    case_convert = (text_type.lower if num3 % 8 > 0 else lambda x: x)
    return '{first}.{last}@x{num:x}.sanitized.net'.format(
        first=case_convert(given_name),
        last=case_convert(surname).replace("'", ''),
        num=num3)


def sanitize_username(value):
    if not value:
        return value
    (num1, num2) = hash_text_to_ints(value, [16, 32])
    return '{}{:x}'.format(given_names[num1 % given_names_count].lower(), num2)


def sanitize_full_name_en_gb(value):
    if not value:
        return value
    (num1, num2) = hash_text_to_ints(value.strip().lower(), [16, 16])
    return '{} {}'.format(
        given_names[num1 % given_names_count], surnames[num2 % surnames_count])


def sanitize_given_name_en_gb(value):
    if not value:
        return value
    num = hash_text_to_int(value.strip().lower())
    return given_names[num % given_names_count]


def sanitize_surname_en_gb(value):
    if not value:
        return value
    num = hash_text_to_int(value.strip().lower())
    return surnames[num % surnames_count]


given_names = """
Aaron Abbie Abdul Abigail Adam Adrian Aimee Alan Albert Alex
Alexander Alexandra Alice Alison Allan Amanda Amber Amelia Amy Andrea
Andrew Angela Ann Anna Anne Annette Anthony Antony Arthur Ashleigh
Ashley Barbara Barry Ben Benjamin Bernard Beth Bethan Bethany Beverley
Billy Bradley Brandon Brenda Brett Brian Bruce Bryan Callum Cameron Carl
Carly Carol Carole Caroline Carolyn Catherine Charlene Charles Charlie
Charlotte Chelsea Cheryl Chloe Christian Christine Christopher Claire
Clare Clifford Clive Colin Connor Conor Craig Dale Damian Damien Daniel
Danielle Danny Darren David Dawn Dean Deborah Debra Declan Denis Denise
Dennis Derek Diana Diane Dominic Donald Donna Dorothy Douglas Duncan
Dylan Edward Eileen Elaine Eleanor Elizabeth Ellie Elliot Elliott Emily
Emma Eric Fiona Frances Francesca Francis Frank Frederick Gail Gareth
Garry Gary Gavin Gemma Geoffrey George Georgia Georgina Gerald Geraldine
Gerard Gillian Glen Glenn Gordon Grace Graeme Graham Gregory Guy Hannah
Harriet Harry Hayley Hazel Heather Helen Henry Hilary Hollie Holly
Howard Hugh Iain Ian Irene Jack Jacob Jacqueline Jade Jake James Jamie
Jane Janet Janice Jasmine Jason Jay Jayne Jean Jeffrey Jemma Jenna
Jennifer Jeremy Jessica Jill Joan Joanna Joanne Jodie Joe Joel John
Jonathan Jordan Joseph Josephine Josh Joshua Joyce Judith Julia Julian
Julie June Justin Karen Karl Kate Katherine Kathleen Kathryn Katie Katy
Kayleigh Keith Kelly Kenneth Kerry Kevin Kieran Kim Kimberley Kirsty
Kyle Laura Lauren Lawrence Leah Leanne Lee Leigh Leon Leonard Lesley
Leslie Lewis Liam Linda Lindsey Lisa Lorraine Louis Louise Lucy Luke
Lydia Lynda Lynn Lynne Malcolm Mandy Marc Marcus Margaret Maria Marian
Marie Marilyn Marion Mark Martin Martyn Mary Mathew Matthew Maureen
Maurice Max Megan Melanie Melissa Michael Michelle Mitchell Mohamed
Mohammad Mohammed Molly Naomi Natalie Natasha Nathan Neil Nicholas
Nicola Nicole Nigel Norman Oliver Olivia Owen Paige Pamela Patricia
Patrick Paul Paula Pauline Peter Philip Phillip Rachael Rachel Raymond
Rebecca Reece Rhys Richard Ricky Rita Robert Robin Roger Ronald Rosemary
Rosie Ross Roy Russell Ruth Ryan Sally Sam Samantha Samuel Sandra Sara
Sarah Scott Sean Shane Shannon Sharon Shaun Sheila Shirley Sian Simon
Sophie Stacey Stanley Stephanie Stephen Steven Stewart Stuart Susan
Suzanne Sylvia Terence Teresa Terry Thomas Timothy Tina Toby Tom Tony
Tracey Tracy Trevor Valerie Vanessa Victor Victoria Vincent Wayne Wendy
William Yvonne Zoe
""".strip().split()


surnames = """
Abbott Adams Ahmed Akhtar Alexander Ali Allan Allen Anderson Andrews
Archer Armstrong Arnold Ashton Atkins Atkinson Austin Bailey Baker
Baldwin Ball Banks Barber Barker Barlow Barnes Barnett Barrett Barry
Bartlett Barton Bates Baxter Begum Bell Bennett Benson Bentley Berry
Bevan Bibi Birch Bird Bishop Black Blackburn Bolton Bond Booth Bowen
Boyle Bradley Bradshaw Brady Bray Brennan Briggs Brookes Brooks Brown
Browne Bruce Bryan Bryant Bull Burgess Burke Burns Burrows Burton
Butcher Butler Byrne Cameron Campbell Carey Carpenter Carr Carroll
Carter Cartwright Chadwick Chambers Chan Chandler Chapman Charlton Clark
Clarke Clayton Clements Coates Cole Coleman Coles Collier Collins
Connolly Connor Conway Cook Cooke Cooper Cox Craig Crawford Cross
Cunningham Curtis Dale Daly Daniels Davey Davidson Davies Davis Davison
Dawson Day Dean Dennis Dickinson Dixon Dobson Dodd Doherty Donnelly
Douglas Doyle Duffy Duncan Dunn Dyer Edwards Elliott Ellis Evans Farmer
Farrell Faulkner Ferguson Field Finch Fisher Fitzgerald Fleming Fletcher
Flynn Ford Forster Foster Fowler Fox Francis Franklin Fraser Freeman
French Frost Fry Fuller Gallagher Gardiner Gardner Garner George Gibbons
Gibbs Gibson Gilbert Giles Gill Glover Goddard Godfrey Goodwin Gordon
Gough Gould Graham Grant Gray Green Greenwood Gregory Griffin Griffiths
Hale Hall Hamilton Hammond Hancock Hanson Harding Hardy Hargreaves
Harper Harris Harrison Hart Hartley Harvey Hawkins Hayes Haynes Hayward
Heath Henderson Henry Herbert Hewitt Hicks Higgins Hill Hilton Hodgson
Holden Holland Holloway Holmes Holt Hooper Hope Hopkins Horton Houghton
Howard Howarth Howe Howell Howells Hudson Hughes Humphreys Humphries
Hunt Hunter Hurst Hussain Hutchinson Hyde Ingram Iqbal Jackson James
Jarvis Jenkins Jennings John Johnson Johnston Jones Jordan Joyce Kaur
Kay Kelly Kemp Kennedy Kent Kerr Khan King Kirby Kirk Knight Knowles
Lamb Lambert Lane Law Lawrence Lawson Leach Lee Lees Leonard Lewis
Little Lloyd Long Lord Lowe Lucas Lynch Lyons Macdonald Mahmood Mann
Manning Marsden Marsh Marshall Martin Mason Matthews May McCarthy
McDonald McKenzie McLean Mellor Metcalfe Miah Middleton Miles Miller
Mills Mistry Mitchell Moore Moran Morgan Morley Morris Morrison Morton
Moss Murphy Murray Myers Nash Naylor Nelson Newman Newton Nicholls
Nicholson Nixon Noble Nolan Norman Norris North Norton O'Blake O'Buckley
O'Chamberlain O'Hobbs O'Thompson Oliver Osborne Owen Owens Page Palmer
Parker Parkes Parkin Parkinson Parry Parsons Patel Patterson Payne
Peacock Pearce Pearson Perkins Perry Peters Phillips Pickering Pollard
Poole Pope Porter Potter Potts Powell Power Pratt Preston Price
Pritchard Pugh Quinn Rahman Randall Read Reed Rees Reeves Reid Reynolds
Rhodes Rice Richards Richardson Riley Roberts Robertson Robinson Robson
Rogers Rose Ross Rowe Rowley Russell Ryan Sanders Sanderson Saunders
Savage Schofield Scott Shah Sharp Sharpe Shaw Shepherd Sheppard Short
Simmons Simpson Sims Sinclair Singh Skinner Slater Smart Smith Spencer
Stanley Steele Stephens Stephenson Stevens Stevenson Stewart Stokes
Stone Storey Sullivan Summers Sutton Swift Sykes Talbot Taylor Thomas
Thomson Thornton Thorpe Todd Tomlinson Townsend Tucker Turnbull Turner
Tyler Vaughan Vincent Wade Walker Wall Wallace Wallis Walsh Walters
Walton Ward Warner Warren Waters Watkins Watson Watts Webb Webster Welch
Wells West Weston Wheeler White Whitehead Whitehouse Whittaker Wilkins
Wilkinson Williams Williamson Willis Wilson Winter Wong Wood Woods
Woodward Wright Wyatt Yates Young
""".strip().split()

given_names_count = len(given_names)
surnames_count = len(surnames)
