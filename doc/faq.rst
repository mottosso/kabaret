

---
FAQ
---	

* **Where does the name 'Kabaret' come from?**
	Kabaret is the open sourcing of the Supamonks Studio development. 
	Our in-house softwares and tools are named with girl firstnames like:
		* Becassine - she let you bake an animation scene ('bake a scene')
		* Rebeka - she let you bake in batch.
		* Trinity - she stores tree shaped data on disk
		* Naomie - she deals the naming conventions
		* Debby - she's the interface to the DataBase
		* Etc...
	We decided to not push those names to the open source version but
	we wanted to keep an hint of girl power :)
	
	Also, we like the French Touch it gives.
	
* **Where does the Kabaret logo come from?**
	The logo draws a strikethrough 'K' symbol.
	
	It's based on a phonetical pun in French.
	
	In French "a kabaret" is "un cabaret". It is phonetically the same as "un K barre'" which in
	English means "a strikethrough 'K'".
	
	It so happens that a strikethrough 'K' is the symbol of the Laos money, the 
	`Loa Kip <http://en.wikipedia.org/wiki/Lao_kip>`_.
	The Laos is a communalist society where the concept of possession is unknown 
	and the word for "mine" is the same as the word for "yours".
	This is a great match with our open source spirit.
	
	We enjoy the idea that branding the Loa Kip could put Laos in focus and help this great country.

	Laos is the most heavily bombed country in the world. They need your help and you should
	`donate to help with the Lao UXO eradication efforts <http://www.uxolao.org/Donating.html>`_.
		
* **Why not a Web app? Aren't you reinventing the wheel?**
	The web technology is considerably more advanced than what we face everyday in the CG industry.
	Most efforts nowadays are on binding the two worlds together. There has been success in this adventure.
	
	But those technologies have their drawbacks:
		* They are meant for very large collaboration. The overhead is too expensive when you work 
		  with a small team (<50).
		* They need Gurus to setup and manage. You can't just throw an Hapache server and cross your 
		  fingers hopping it won't drop if *everything* in the studio relies on it.
		* Unless you invest a lot, the web server option will create a bottleneck on the network bandwidth
		  and a point of massive failure in the network architecture.
	
	On the other side, Python is massively adopted in our industry and Python does a really good job
	at inter-process communications and multiprocessing (No. don't throw the GIL topic here. Please :P).
	
	It has been an great experience to dive into distributed software and to bring asynchronous 
	call to a Qt GUI.
	
	Thanks to *Irmen de Jong* we did not invent any wheel for that. We just leveraged the awesome 
	`Pyro4 <http://packages.python.org/Pyro4/>`_ library.
	 
	This does not mean that Kabaret is out of reach from your browser. We plan on providing web based UI
	for some of the services a Kabaret project provides. But it is not a primary goal.
	
* **Why not ZeroMQ?**
	We are trying hard to launch an open source and collaborative effort in the CG Production Tracking 
	and Asset Management.
	
	We have no choice but supporting all the major platforms and DCCs: the goods and the craps.
	So we need Kabaret to run smoothly on Windows and with Maya.
	
	Another concern we have is the easiness of installation of the various Kabaret components. 
	The interpreted aspect of python is a great asset in this area: non compilation!
	
	We had to drop all the ZeroMQ based code when we 
	discovered (see `here <http://forums.cgsociety.org/showthread.php?t=1063178>`_
	and `there <http://forums.cgsociety.org/showthread.php?p=7393148#post7393148>`_ for a glimpse)
	that Maya for windows embeds a *"modified python in a non standard way"* and needs you to
	compile any extension against it.
	
	It has been a tough decision but we choose to use only pure-python library for the Kabaret core.
	
	Beside, Pyro4 rocks hard and does the job extrimely well considering it is written in 100% pure
	python.
	 
* **Why not Zoiberg?**
	I see what you did here: `(V)(;,,;)(V) <http://knowyourmeme.com/memes/futurama-zoidberg-why-not-zoidberg>`_

* **Do I want to use Kaberet Studio or build up my own solution?**
	We hope that Kabaret Studio is flexible and powerful enough for most cases. We would rather enhance 
	the Kabaret Studio so that it covers your need.
	
	But we also understand that some studio may need to blend their own solutions with Kabaret Framework, 
	or just can't open their in-house code.
	
	This is why Kabaret's core (the Framework) has been decoupled from the solution we use (the Studio).
	So that you can dose the amount of Kabaret you embrace.
	
	One can even use some engines (flow, naming, etc...) without any other Kabaret involvement.
	The engines used in the Kabaret Studio will always be available with no dependency on any other Kabaret
	package.
	
	We hope that this will help you use the Kabaret components without copying the code but with a clean 
	easy_install dependency, so that you can share with everybody your feedbacks, ideas and colaboration.

* **Where do I get support?**
	There are two forums:
		* `kabaret-studio <http://groups.google.com/group/kabaret-studio>`_ for Users and TDs working 
		  with the Kabaret Studio.
		* `kabaret-dev <http://groups.google.com/group/kabaret-dev>`_ for the TDs and Developers using any
		  Kabaret packages.


	