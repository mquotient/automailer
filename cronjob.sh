echo "Running the automailer script"
mailer_home="/home/linus/Build/automailer"
exec="ipython"
mail_file="automailer.py"

current_dir=`pwd`
cd $mailer_home
date >> .runinfo
ipython automailer.py
cd $current_dir

echo "Finished running the automailer script"
