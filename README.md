# LDIF bulk user and group generator for FreeIPA insertion
Generate large amount of users and/or groups in LDIF format for FreeIPA consumption

## Requirements
`python3.6+`

## Usage
1. Install requirements from `requirements.txt` (preferably in a venv)
```shell
python3 -m pip install -r requirements.txt
```

2. Generate a LDIF file using
```shell
python3 generate.py -b "dc=ipa,dc=test" -nu 120 -ng 5 -o test.ldif
```
where:
- `-b`: base DN
- `-nu` : number of users to generate (can be 0)
- `-ng` : number of groups to generate (can be 0)
- `-o` : the output file

3. Transfer the LDIF file to target freeipa server
4. `kinit admin`
5. `ipa config-mod --enable-migration=TRUE`
6. ```
   ldapadd -x -H ldap://localhost:389  -D "cn=Directory Manager" -w <PASSWORD> -c -f <FILENAME>.ldif
   ```
7. ```
   ipa migrate-ds ldap://localhost:389 --with-compat --user-container="cn=users,cn=accounts,dc=ipa,dc=test"
    ```
