import argparse
import random
import string

import names

parser = argparse.ArgumentParser("LDIF generator for mass user addition to "
                                 "FreeIPA")
parser.add_argument("-b", "--base_ou", help="Base DN",
                    type=str,
                    required=True)
parser.add_argument("-o", "--output", help="Output LDIF file",
                    type=str,
                    required=True)
parser.add_argument("-nu", "--number_of_users",
                    help="Number of user entries to be generated",
                    type=int,
                    required=True)
parser.add_argument("-ng", "--number_of_groups",
                    help="Number of group entries to be generated",
                    type=int,
                    required=True)


class LDIFGenerator:
    def __init__(self, base, no_users, no_groups, output):
        self.base = base
        self.no_users = no_users
        self.no_groups = no_groups
        self.output = output

        self.people = {}
        self.groups = {}
        self.tree = {}

        self._prepare_structures()

    def _prepare_structures(self):
        # prepare people
        self.people['dn'] = 'ou=people,' + self.base
        self.people['objectClass'] = 'organizationalUnit'
        self.people['ou'] = 'people'
        self.people['leafs'] = {}

        # prepare groups
        self.groups['dn'] = 'ou=groups,' + self.base
        self.groups['objectClass'] = 'organizationalUnit'
        self.groups['ou'] = 'groups'
        self.groups['leafs'] = {}

        # prepare the tree structure
        self.tree['dn'] = self.base
        self.tree['objectClass'] = 'domain'
        self.tree['leafs'] = {}
        self.tree['leafs']['people'] = self.people
        self.tree['leafs']['groups'] = self.groups

    def _generate_person(self):
        person = {}

        name = names.get_full_name()
        uid = (''.join(name.split(' ')).lower())
        person['dn'] = f"uid={uid},ou=people,{self.base}"
        person['objectClass'] = ["inetOrgPerson", "posixAccount"]
        person['uid'] = uid
        person['cn'] = name
        person['uidNumber'] = random.randrange(911400001,
                                               911400001 + self.no_users)
        person['gidNumber'] = random.randrange(911400001,
                                               911400001 + self.no_users)
        person['homeDirectory'] = f"/home/{uid}"
        person['userPassword'] = "".join(random.sample(
            string.ascii_letters, 8))
        person['displayName'] = name
        person['givenName'] = name.split(' ')[0]
        person['sn'] = name.split(' ')[1]
        return person

    def _generate_group(self):
        group = {}

        # group name consist of group + random string with length enough
        # to avoid duplicates
        random_appendix = "".join(random.sample(
            string.ascii_lowercase, len(str(self.no_groups))))
        name = f"group{random_appendix}"
        group['dn'] = f"cn={name},ou=groups,{self.base}"
        group['objectClass'] = 'groupOfNames'
        group['cn'] = name
        group['member'] = []

        all_available_users = list(self.tree['leafs']['people']['leafs'].keys())
        no_members = random.randint(1, self.no_users)

        for i in range(no_members):
            member_uid = random.choice(all_available_users)
            member = self.tree['leafs']['people']['leafs'][member_uid]['dn']
            while member in group['member']:
                member_uid = random.choice(all_available_users)
                member = self.tree['leafs']['people']['leafs'][member_uid]['dn']
            group['member'].append(member)

        return group

    def _print_tree(self, output, tree=None):
        if tree is None:
            # for handling recursion
            tree = self.tree

        if 'dn' in tree:
            # dn must print first
            output.write(f"dn: {tree['dn']}\n")
            for key, val in tree.items():
                if key in ['dn', 'leafs']:
                    continue
                if isinstance(val, list):
                    # multivalued attribute
                    for entry in val:
                        output.write(f"{key}: {entry}\n")
                else:
                    # single-valued attribute
                    output.write(f"{key}: {val}\n")
            output.write("\n")
            if 'leafs' in tree:
                self._print_tree(output, tree['leafs'])
        else:
            if 'people' in tree:
                self._print_tree(output, tree['people'])
                tree.pop('people')
            if 'groups' in tree:
                self._print_tree(output, tree['groups'])
                tree.pop('groups')
            for entry in tree:
                self._print_tree(output, tree[entry])

    def generate_tree(self):
        # generate users and append them to the tree
        for _ in range(self.no_users):
            tree_people_p = self.tree['leafs']['people']['leafs']
            person = self._generate_person()
            while person['uid'] in tree_people_p:
                person = self._generate_person()
            tree_people_p[person['uid']] = person

        # generate groups and append them to the tree
        for _ in range(self.no_groups):
            tree_groups_p = self.tree['leafs']['groups']['leafs']
            group = self._generate_group()
            while group['cn'] in tree_groups_p:
                group = self._generate_group()
            tree_groups_p[group['cn']] = group

        with open(self.output, "w") as output:
            self._print_tree(output)


if __name__ == '__main__':
    args = parser.parse_args()

    ldif_gen = LDIFGenerator(args.base_ou,
                             args.number_of_users,
                             args.number_of_groups,
                             args.output)
    ldif_gen.generate_tree()
