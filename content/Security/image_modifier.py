import re
import os

file_paths = [
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Pentesting/Hackthebox/ActiveDirectory/BLACKFIELD.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Pentesting/Hackthebox/ActiveDirectory/ESCAPE.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Pentesting/Hackthebox/ActiveDirectory/FOREST.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Pentesting/Hackthebox/ActiveDirectory/MANAGER.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Pentesting/Hackthebox/ActiveDirectory/MANTIS.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Pentesting/Hackthebox/ActiveDirectory/OUTDATED.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Pentesting/Hackthebox/ActiveDirectory/REEL.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Pentesting/Hackthebox/ActiveDirectory/SAUNA.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Pentesting/Hackthebox/Linux/AGILE.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Pentesting/Hackthebox/Linux/ARMAGEDDON.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/BACKDOOR.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/BASHED.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/BLOCKY.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/BRAINFUCK.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/CAP.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/CODIFY.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/COZYHOSTING.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/CRONOS.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/CURLING.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/DELIVERY.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/DEVOOPS.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/DEVVORTEX.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/FRIENDZONE.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/HAWK.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/IRKED.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/JARVIS.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/KNIFE.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/KOTARAK.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/LIGHTWEIGHT.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/META.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/METATWO.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/NETWORKED.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/NIBBLES.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/NINEVEH.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/PANDORA.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/PAPER.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/PILGRIMAGE.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/POISON.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/PRESSED.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/REDDISH.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/SEA.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/SENSE.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/SHOCKER.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/SHOPPY.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/SOCCER.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/SOLIDSTATE.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/TABBY.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/TRICK.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/TWOMILLION.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Linux/VALENTINE.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/ACUTE.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/ARCTIC.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/BART.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/BOUNTY.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/CONCEAL.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/DEVEL.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/DRIVER.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/FALAFEL.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/HEIST.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/JEEVES.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/JERRY.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/LOVE.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/NETMON.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/REMOTE.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/SERVMON.md",
    "/Users/seonwookim/Documents/Programming/seonwookim92.github.io/content/Security/Hackthebox/Windows/TALLY.md"
]

regex_pattern = r'!\[(.*?)\]\\(public/Images/(.*?)/([^/]+)\\)'
replacement_string = r'![\1](\3)'

for file_path in file_paths:
    print(f"Processing file: {file_path}")
    try:
        # Read file content
        read_response = default_api.read_file(absolute_path=file_path)
        file_content = read_response.get('read_file_response', {}).get('output')

        if file_content is None:
            print(f"Could not read content from {file_path}. Skipping.")
            continue

        # Perform the regex replacement
        new_content = re.sub(regex_pattern, replacement_string, file_content)

        if new_content != file_content:
            print(f"Changes detected in {file_path}. Writing updated content.")
            # Write updated content back to file
            default_api.write_file(file_path=file_path, content=new_content)
        else:
            print(f"No changes needed for {file_path}.")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

print("Image path modification complete for all identified Markdown files.")