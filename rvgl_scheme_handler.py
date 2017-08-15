#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, sys, sys, glob, shutil, configparser, subprocess, ctypes
from tkinter import filedialog, messagebox
import beautifulscraper as bs
import zipfile, lzma

def is_admin():
	try:
		return ctypes.windll.shell32.IsUserAnAdmin()
	except:
		return False


def warning(install_name):
    if not messagebox.askokcancel("RVGL web action", "This will modify your Re-Volt install, are you sure?\nYou are about to install "+install_name+"."):
        exit(0)

    try:
        os.mkdir("temp")
    except FileExistsError:
        pass


def finished():
    os.rmdir("temp")
    messagebox.showinfo("Finished", "Everything is DONE!")
    fix_cases()
    exit(0)
    

def fix_cases():
    if os.name == "posix":
        for file in glob.iglob(r"**", recursive=True):
            try:
                os.rename(file, file.lower())
            except OSError:
                try:
                    shutil.rmtree(file.lower())
                except NotADirectoryError:
                    os.remove(file.lower())
                os.rename(file, file.lower())

def install_month():
    warning("Month tracks")
    
    scrapper = bs.BeautifulScraper()
    webpage = scrapper.go("https://www.revoltrace.net/month_tracks.php")

    for a in webpage.find_all(attrs={"class": "downloadTrack"}):
        url = bs.urlparse(a.get("href"))
        if url.netloc == "revoltzone.net":
            track_id = url.path.split("/")[2]
            inter_url = "http://revoltzone.net/sitescripts/dload.php?id="+track_id
            inter = bs.urllib2.urlopen(inter_url)
            
            true_url = inter.getheader("Location")
        if url.netloc == "revoltxtg.co.uk":
            true_url = url.geturl()
        
        install_asset(true_url, batch=True)
    
    finished()

    
def install_asset(URL_encoded, batch=False):
    URL = bs.urllib2.unquote(URL_encoded)
    URL = bs.urllib2.unquote(URL)
    
    URL = URL[:8]+bs.quote(URL[8:])
    
    filename = URL[8:].split("/")[-1]
    asset_name = filename.split(".")[0]
    
    if not batch:
        warning(asset_name)
    
    print("Downloading "+asset_name+" from "+URL)
    bs.urllib2.urlretrieve(URL, "temp/"+asset_name+".zip")
    
    print("Extracting "+filename)
    file_uri = 'temp/'+filename
    
    filetype = filename.split(".")[-1]
    
    if filetype == "zip":
        with zipfile.ZipFile(file_uri, "r") as z:
            z.extractall()
    
    if filetype == "7z":
        with lzma.LZMAFile(file_uri, "r") as z:
            z.extractall()
    
    os.remove(file_uri)
    
    if not batch: finished()


def launch(*args):
	if os.name == "posix":
		os.execv("./rvgl", ("rvgl", *args))
	else:
		os.execv("rvgl.exe", ("rvgl.exe", *args))


def join(IP="", *args):
    launch("-lobby", str(IP), *args)


def main():
    if os.name == "posix": # Linux
        config = configparser.ConfigParser()
        if not config.read("scheme_handler_settings.ini"):
            with open(os.environ["HOME"]+"/.local/share/applications/rvgl_scheme_handler.desktop", "w") as desktop_file:
                desktop_file.write("[Desktop Entry]\n\
                                    Version=1.0\n\
                                    Type=Application\n\
                                    Exec="+os.path.abspath(".")+"/rvgl_scheme_handler.py %u\n\
                                    Icon="+config["RVGL"]["install_dir"]+"/icons/256x256/apps/rvgl.png\n\
                                    StartupNotify=true\n\
                                    Terminal=false\n\
                                    Categories=Utility;\n\
                                    MimeType=x-scheme-handler/rvgl\n\
                                    Name=RVGL scheme handler\n\
                                    Comment=Launch RVGL")
            subprocess.run(("update-desktop-database", os.environ["HOME"]+"/.local/share/applications"))
            messagebox.showinfo("No configuration found", "I did not found the configuration file, please move to your RVGL install folder then confirm")
            config["RVGL"] = {"install_dir": filedialog.askdirectory()}
            with open('scheme_handler_settings.ini', 'w') as configfile:
                config.write(configfile)
        rvgl_dir = config["RVGL"]["install_dir"]
    else: # Windows
        import winreg
        
        try:
            key = winreg.OpenKeyEx(winreg.HKEY_CLASSES_ROOT, "rvgl")
            rvgl_dir = winreg.QueryValue(key, "directory")
        except OSError:
            if is_admin():
                messagebox.showinfo("No configuration found", "I did not found the configuration file, please move to your RVGL install folder then confirm")
                rvgl_dir = filedialog.askdirectory()
                
                winreg.SetValue(winreg.HKEY_CLASSES_ROOT, "rvgl", winreg.REG_SZ, "RVGL:// custom handler")
                key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "rvgl")
                winreg.SetValue(key, "URL Protocol", winreg.REG_SZ, "")
                winreg.SetValue(key, "directory", winreg.REG_SZ, rvgl_dir)
                shell = winreg.CreateKey(key, "shell")
                open_key = winreg.CreateKey(shell, "open")
                winreg.SetValue(open_key, "command", winreg.REG_SZ, '"'+sys.argv[0]+'" "%1"')
            else:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, "", None, 1)
                exit(0)

    if len(sys.argv)>=2:
        os.chdir(rvgl_dir)

        URI_raw = " ".join(sys.argv[1:])
        URI = URI_raw[7:].split("/")
        function_name = URI[0]
        args = URI[1:] if len(URI)>=2 else ()

        functions = {"launch": launch,
                     "join": join,
                     "install_asset": install_asset,
                     "install_month": install_month}

        functions[function_name](*args)

if __name__ == '__main__':
    main()
