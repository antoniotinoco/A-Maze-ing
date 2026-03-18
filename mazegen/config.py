def config(path="config.txt"):
    keys = ["WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"]
    config = {}

    with open(path, "r") as file:
        for line in file:
            line = line.strip()

            # skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # check format
            if "=" not in line:
                raise ValueError("Invalid line format")

            try:
                a, b = line.split("=", 1)
                a = a.strip()
                b = b.strip()
            except ValueError:
                raise ValueError("Error during parsing")

            # validate key  / duplciate 
            if a not in keys:
                raise ValueError(f"Invalid or duplicate key: {a}")
            if not b:
                raise ValueError(f"{a} cannot be assigned an empty value")

            # store
            config[a] = b
            keys.remove(a)

    # check missing keys
    if keys:
        raise ValueError(f"Missing keys: {keys}")

    return config
    

def validate_config(config: dict):
    # WIDTH HEIGHT
    try:
        WIDTH = int(config["WIDTH"])
        HEIGHT = int(config["HEIGHT"])
    except ValueError:
        raise ValueError("WIDTH and HEIGHT must be integers")
        
    if WIDTH <= 0:
        raise ValueError("WIDTH must be a positive integer")
    if HEIGHT <= 0:
        raise ValueError("HEIGHT must be a positive integer")

    config["WIDTH"] = WIDTH
    config["HEIGHT"] = HEIGHT
    
    # PERFECT
    PERFECT = config["PERFECT"]
    if PERFECT == "True":
        config["PERFECT"] = True
    elif PERFECT == "False":
        config["PERFECT"] = False
    else:
        raise ValueError("PERFECT must be True or False")
        
    # ENTRY + EXIT
    try:
        x, y = config["ENTRY"].split(",")
        x = int(x)
        y = int(y)
        config["ENTRY"] = (x, y)
    except ValueError:
        raise ValueError("ENTRY must be in format x,y with integers")

    try:
        t, z = config["EXIT"].split(",")
        t = int(t)
        z = int(z)
        config["EXIT"] = (t, z)
    except ValueError:
        raise ValueError("EXIT must be in format x,y with integers")
    

    return config
    