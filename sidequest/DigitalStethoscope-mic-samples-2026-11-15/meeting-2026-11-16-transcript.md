# Meeting of 16 November 2026: transcript

- **When:** 16 November 2026, 10:33 to 10:58 (about 25 minutes).
- **Source:** PrivateFlow 0.4.0, local transcription, languages `en,de,es`. Original record:
  `C:\Users\nicop\AppData\Local\PrivateFlow\meetings\e88f2ffdf2934399a923f56f9c0c3cc4\meeting.json`.
- **Only the remote speaker is in the transcript.** Nico's microphone channel was recorded as digital silence for the
  whole meeting (PrivateFlow issue [#27](https://github.com/DemonicPsychoII/private-flow/issues/27)), so every answer
  from Nico is missing and cannot be recovered. The last 20 s of the microphone channel were also never transcribed.
- **Accuracy:** machine transcription, not corrected. Known mishearing: "Sapphire" means Zephyr.

## TL;DR

The remote speaker doubted that the microphone itself overloads and asked for the cause to be located before
anything is damped or filtered. They also asked for the filter work to be evaluated on recorded files with numbers,
not by listening on one's own chest.

**Doubts and questions about the overload**

- They could not imagine that the microphone is at its limit, because such microphones are built for speech, which
  they consider far louder than what arrives through the tube.
- Check the 24-bit values written by DMA: are they really at the limit?
- If not, the overload may come from further back: the output stage or the speaker.
- Check how the samples are stored, left- or right-aligned. Shifting left by 8 bits would be a gain of 256 that the
  output might not handle.
- If it really is the microphone, build in something that damps at the front.
- They asked how "the AI" removed the crackle: by dropping values, zeroing them, or repeating the previous value.
- Their own analog system overloads in the amplifiers (gain of a few thousand), not at the microphone. They also
  mentioned that their own I2S/DMA driver once clicked every 5 to 6 seconds because DMA was not filled cleanly.

**Advice on method**

- Measuring on your own chest mostly tests contact pressure and position, not the filter.
- Record uncompressed WAV files and apply the filters to those files, in Python or MATLAB.
- Judge by listening if you like, but also look at the spectrum (FFT) and state in numbers why one filter is better.
- Start writing the thesis documentation alongside the work.

**Offers**

- An external 24-bit sound card on loan (about 8 EUR) to feed the signal into the PC.
- An exciter board, also available through Mr. Till.
- Access to a course that has a browser "Audioscope" with oscilloscope view, FFT and a few filters.

**Dates**

- Next meeting next week at the same time; Nico sends the invitation, with the reminder set five minutes earlier.
- Nico's stated goal: finished in two weeks.

**How the measurements of the same day answer the doubts** (details in [README.md](README.md))

- The raw 24-bit values are at the limit: the microphone delivers its extreme codes, flat for up to 16 ms.
- The overload is not audible sound but slow pressure in the sealed air volume, over 90 % of it below 20 Hz.
- The alignment suspicion was right in kind: the samples were one bit too far left (a factor of 2, not 256).
- Nothing was dropped or replaced to remove the crackle; the samples are now read one bit clock earlier.

## Transcript (remote speaker only)

Times are minutes and seconds from the start of the recording.

- `00:40` Okay, super.
- `01:34` Also wir haben es luftig gemacht, wirklich komplett.
- `02:03` Okay, dann müssen Sie halt da mit Ihrer Verstärkung runtergehen.
- `02:13` Also Sie meinen, das ist jetzt, ich kenne das Mikrofon, das Sie haben, was hat das denn alles?
- `02:20` Kann man bei dem eine Gain einstellen?
- `02:25` Okay.
- `02:27` Also wenn sie da wirklich zu gut sind,
- `02:29` das Problem haben wir jetzt,
- `02:29` wir nicht...
- `02:39` Ist es wirklich das Mikrofon, das da an Anschlag geht?
- `02:44` Also wenn Sie sich die Werte mal anschauen, die in Ihrem DMA geschrieben werden, dann sind das 24-Bit, glaube ich.
- `02:52` AD-Wandlerwerte, die sie da kriegen.
- `02:55` Und die sind wirklich dann im Anschlag.
- `02:58` Also das 24 wird, das sind ja 16 Millionen.
- `03:01` Ne, doch, 16 Millionen, oder?
- `03:07` Da müssen wir mal wirklich schauen, ob das jetzt die Werte sind vom Mikrofon, die in Anschlag gehen.
- `03:14` Und das kann ich mir nicht vorstellen.
- `03:16` Weil die ganzen Mikrofone, die sind ja ausgelegt wirklich auf Sprache.
- `03:20` Und da ist es ja viel, viel, viel lauter wie das, was sie jetzt über ihren Schlauch hören.
- `03:24` Das ist ja Welten weniger.
- `03:31` Und wenn jetzt da die Werte nicht am Anschlag sind,
- `03:37` dann vermute ich, dass das Übersteuern von ihrem Lautsprecher herankommt.
- `03:43` Dass der irgendwie...
- `03:44` Also das mal nachvollziehen, wo kommt es denn her?
- `03:50` Ist es wirklich das Mikrofon oder ist es irgendwas dazwischen oder ist es Ihr Lautsprecher?
- `03:55` Verarbeiten Sie wirklich die 24-Bit-Werte dann oder machen Sie da 16-Bit-Werte draus?
- `04:38` Okay.
- `04:54` Also wie gesagt, ich würde schauen, wo es herkommt.
- `04:58` Und dann, also wenn es wirklich vorne vom Mikrofon kommt,
- `05:01` dann müssen sie da was Dämpfendes einbauen.
- `05:03` Ja, aber das kann ich mir nicht vorstellen.
- `05:06` Also wir haben das übersteuern, das kriegen wir auch hin,
- `05:08` aber nicht vom Mikrofon, sondern...
- `05:11` weiter hinten, also wir haben ja
- `05:13` ein analogisches System auch.
- `05:16` Ich habe ein digitales, aber wir haben auch ein analogisches
- `05:18` aufgebaut und beim Analogen, da kriegen wir das
- `05:20` Übersteuern dann von unseren Verstärkern.
- `05:22` Da haben wir halt eine Verstärkung drin, ich glaube
- `05:24` von ein paar tausend, also
- `05:28` wie das Signal verstärkt wird.
- `05:31` Und das haben ja sie nicht,
- `05:32` weil sie haben ja ihr komplett digitales System.
- `05:35` Die haben ja den MEMS vorne drin.
- `05:39` Aber auch da kann ich...
- `05:40` Also so rein vom Bauchgefühl her,
- `05:43` ich kann es mir nicht vorstellen,
- `05:43` dass das das Mikrofon ist.
- `05:46` Vielleicht auch nochmal anschauen, wie sie abgelegt werden, die Daten.
- `05:50` Also sind die rechtsbündig, sind sie linksbündig?
- `05:54` Nicht, dass sie...
- `06:10` Das vielleicht nochmal anschauen.
- `06:13` Das müssen wir dann auch nochmal zeigen.
- `06:16` Wieso müssen die von linken Kanal
- `06:18` left sein?
- `06:20` Also das höchstwertige Bit ist dann das Bit 32.
- `06:25` Das 24. Bit wird zum Bit 32.
- `06:29` Aber das verstärkt ja dann.
- `06:32` Also da machen sie eine Verstärkung dann von...
- `06:35` weiß nicht wie viel. Also 8
- `06:37` geschifftet ist ja 2 hoch 8 multipliziert.
- `06:40` Also sie verstärken dann um 256.
- `07:52` Okay. Und was verwenden Sie da? Das ist ein Treiber von dem Sapphire, oder?
- `08:04` Nee, das habe ich selber gemacht,
- `08:09` weil das nicht schade funktioniert hat bei mir.
- `08:11` Also ich habe immer einen Knacksen dann gehabt.
- `08:13` Ich weiß nicht, ob sie das auch haben.
- `08:15` Also so alle...
- `08:18` So alle 5-6 Sekunden hat er einfach klack, klack gemacht.
- `08:22` Der hat die Daten nicht sauber befüllt in den DMA rein.
- `08:29` Aber weiß ich nicht.
- `08:31` Das ist auch schon ein paar Monate her.
- `08:33` Also gibt es wahrscheinlich schon wieder ein Update.
- `08:52` Genau, da hat sich auch schon.
- `08:56` Also da kam es halt wirklich vom Datentransfer.
- `09:00` Genau.
- `09:12` Okay.
- `09:20` Okay, ja, ist logisch nachvollziehbar.
- `09:26` Auch gefühlt sagt man, nee.
- `09:28` Aber mal gucken.
- `09:32` Genau, und das mit dem links schieben, das würde ich mir auch nochmal anschauen, weil wenn Sie es wirklich links schieben, ist es einfach eine Verstärkung und das kann sein, dass da Ihr Lautsprecher dann das auch nicht mitmacht. Was ist das für ein IC, wo Sie da verwenden dann?
- `09:51` Für Ihren Lautsprecher?
- `09:54` Oder geben Sie direkt das...
- `10:13` Ah.
- `10:40` Yep.
- `10:54` Ja, das sieht ganz gut aus.
- `10:56` Gut.
- `10:59` Okay, das heißt, Sie hören jetzt was, haben noch ein paar Knacksprobleme mit drinnen,
- `11:06` was vielleicht gar nicht so schlecht ist wie Ihre Software,
- `11:08` weil dann können Sie gleich überlegen, wie kann man denn die Knacksgeräusche wegbringen.
- `11:13` Okay.
- `11:39` Genau, Ursache bekämpfen ist immer besser.
- `11:43` Wie hat die KI das gelöst?
- `11:44` Die hat einfach die Werte dann...
- `11:47` die so groß sind, weggelassen oder was macht sie da?
- `11:51` Null raus oder Mittelwert, den Wert von vorher übernehmen.
- `12:07` Also ist gut mit mir.
- `12:09` Ich wollte eigentlich das erreichen, was ich glaube erreicht habe.
- `12:12` Sie schauen sich das nochmal an.
- `12:38` Was müssen Sie jetzt dann nur umsetzen? Was fehlt noch?
- `13:39` It's a problem.
- `13:51` Okay, cool. Sie können das Signal ja direkt auf Ihren Audio-In von Ihrem Laptop geben, oder? Oder von Ihrem PC?
- `14:13` Ja, aber was? Okay, dann kommen Sie gerne bei mir vorbei, dann leih ich Ihnen...
- `14:22` So was, sieht man das?
- `14:25` Kostet 8 Euro, so eine externe
- `14:27` 24-Bit-Soundkarte und dann
- `14:30` können sie das an ihren Laptop anschließen
- `14:32` und dann haben sie, also dann
- `14:33` können sie halt auch mit den Daten
- `14:36` sich die Sachen gleich anschauen und können
- `14:38` auf ihrem PC die Filter ausprobieren.
- `14:41` Das finde ich ganz geschickt.
- `14:43` Sie müssen es halt nicht immer auf Ihrem ESP dann runterladen,
- `14:46` sondern können sich live die Daten dann auch anschauen.
- `14:51` Was haben Sie denn jetzt für ein normal,
- `14:54` also Sie messen bei sich dann immer oder?
- `14:58` Okay.
- `15:04` Wie machen Sie das mit den Filtern jetzt dann?
- `15:06` Wollen Sie das dann auf dem ESPE ausprobieren oder wie haben Sie sich das gedacht?
- `15:50` Okay. Ist das ein guter Test? Was würden Sie denn sagen? Ist der reproduzierbar? Ist der...
- `16:05` Irgendwie durch was belegen sie denn, dass der Filter jetzt gut ist und dass der andere Filter nicht so gut ist?
- `16:28` Okay.
- `16:57` Was wollen wir denn überprüfen mit
- `17:00` den Tests, die sie jetzt gerade machen.
- `17:02` Wir wollen ja die Filterqualität testen, oder?
- `17:07` Und jetzt behaupte ich, wenn sie das bei sich selber messen
- `17:10` und auf die Brust anlegen,
- `17:12` dann prüfen sie da mehr ihren Anpressdruck und die Position.
- `17:17` wie das eigentliche Filter.
- `17:20` Wie könnte man das umgehen,
- `17:21` dass wir das nicht mehr haben?
- `17:22` Und ich mache jetzt nicht
- `17:22` auf den Exciter da raus,
- `17:24` auf so ein Körpermodell,
- `17:26` sondern das kann man ja gar nicht
- `17:26` auch anders machen.
- `17:27` Was wäre denn so eine Idee?
- `17:47` you know,
- `17:48` Also das würde ich Ihnen empfehlen, dass Sie, das ist rein softwaretechnisch,
- `17:52` dass Sie einfach gerne bei sich auch mal eine Datei erzeugen, eine, die jetzt nicht komprimiert unbedingt,
- `18:03` eine Wave-Datei und dann die Filter auf die anwenden.
- `18:10` Und gerne können Sie das qualitativ machen,
- `18:16` also indem Sie es nur bewerten, ist das jetzt besser oder schlechter wie das...
- `18:20` vorhergehende. Aber ich finde,
- `18:23` dass in der Bachelorarbeit auch
- `18:25` wirklich sich die
- `18:27` Informationen von dem Signal anschauen sollten.
- `18:32` Was wäre da die Idee?
- `18:33` Was meinen Sie, was für ein Filter...
- `18:35` Ich weiß jetzt nicht, was Sie bei Creative Engineering da alles hatten, auch so systemtheorie-mäßig. Darum frage ich vielleicht ein bisschen doof auch nach, was würden Sie denn da machen? Was könnte man denn da für Informationen nutzen?
- `19:07` Mm-hmm.
- `19:16` Und das würden Sie super sehen, wenn Sie sich das Frequenzspektrum anschauen, oder?
- `19:22` Genau.
- `19:24` Also ich würde wirklich das Signal dann mal in der FFT drüber laufen lassen,
- `19:28` dass Sie sehen, was sind da alles für Frequenzen drinnen.
- `19:31` Und was macht denn jetzt mein Filter mit den Televancen?
- `19:34` Und dann wirklich gerne das qualitativ bewerten.
- `19:37` Ah ja, okay, wenn der Peak da bei 2 Kilohertz ist,
- `19:40` das ist ein Rauschen, das ist ziemlich doof, wenn ich das höre.
- `19:44` Und durch den Filter, den sie dann anwenden, ist das weg
- `19:46` und dann ist es besser.
- `19:47` Und dann haben sie so...
- `19:50` qualitativ das ganze System mal bewertet,
- `19:52` aber Sie können es halt quantitativ dann auch sagen,
- `19:54` der Filter ist jetzt wirklich besser zahlenmäßig
- `19:55` wie der andere Filter.
- `19:59` Und das finde ich gut,
- `20:01` wenn Sie das irgendwie mit einbauen würden könnten.
- `20:04` Ich kann Sie einfach mal in den Kurs bezeichnen.
- `20:07` bei uns mit reinschreiben. Der ist jetzt bei den
- `20:09` Medizintechnikern. Aber da haben wir
- `20:12` einen Audioscope,
- `20:14` habe ich da programmieren lassen, die KI, das habe ich
- `20:16` nicht selber gemacht, aber ich finde, das hat er sehr, sehr schön gemacht.
- `20:20` Und das können Sie
- `20:21` dann auch mal mit dem testen.
- `20:23` Am PC sehen Sie dann
- `20:24` so eine Art Osti-Funktion.
- `20:27` Und auch eine FFT.
- `20:29` Und es gibt ein paar Filter, die sind da schon mit drin.
- `20:32` Und die können es gerne auch erweitern, anders machen.
- `20:35` Aber dann haben sie vielleicht mal so einen Startpunkt
- `20:37` und müssen nicht bei Null anfangen.
- `20:39` Wenn sie es jetzt reichend softwaremäßig machen würden,
- `20:42` ich würde ihnen da vielleicht sogar entweder testen mit...
- `20:47` mit Python, dass sie da was machen,
- `20:50` oder mit Matlab.
- `20:54` Matlab ist für so Dinge wirklich super.
- `21:11` Das wäre super. Das wäre super cool.
- `21:30` Gerne. Ich würde es Ihnen wahrscheinlich auch nicht sagen können,
- `21:32` aber ich höre es mir gerne an und höre es mir an, wenn mir etwas einfällt.
- `21:37` auf jeden Fall.
- `22:02` Ich trage sie mal ein als studentischen Training.
- `22:05` Bloß, dass sie eine andere Rolle haben wie die anderen.
- `22:10` Dann dürften sie jetzt darauf zugreifen können.
- `22:12` Und dann in der Woche...
- `22:27` gibt es einen Audioscope-Link.
- `22:32` Und wenn Sie draufgehen, dann geht eine
- `22:33` Seite auf, die läuft bei uns auf
- `22:35` irgendeinem Rechner und
- `22:44` können Sie dann die Audioquelle wählen von Ihrem PC und sehen dann den Signalverlauf.
- `22:49` Und unten gibt es dann auch die FFT dazu.
- `22:54` Und ich kann Ihnen was Eigenes auch nutzen, wenn Sie was Besseres haben, dann sagen Sie mir es auch.
- `22:58` So als Einstieg ist das vielleicht gar nicht so verkehrt, wenn Sie da was haben.
- `23:05` Gut.
- `23:19` sind sie ja in zwei Wochen fertig.
- `23:25` Ist ihr Ziel. Gut.
- `23:34` Schreiben Sie schon nebenzu ein bisschen was.
- `23:42` Passt.
- `23:43` Aber wenn Sie nebenzu schon dokumentieren, dann ist das super.
- `23:46` Wunderbar.
- `23:48` Toll, freut mich, dass Sie schon was hören.
- `23:50` Finde ich super.
- `23:52` dass sie das Audiosignal bekommen über DMA,
- `23:55` weiterreichen, aufteilen, Stereo an.
- `24:05` Wann machen wir nächsten Termin?
- `24:19` Wenn Sie wollen, sehr gerne.
- `24:21` Ja, können wir sehr gerne machen.
- `24:24` Gleiche Zeit.
- `24:28` Dann schicken Sie mir einfach Einladung und dann sehen wir uns nächste Woche.
- `24:35` Ja, dann machen Sie die Erinnerung fünf Minuten früher, also machen Sie 10 Uhr, keine Ahnung, was war.
- `24:42` Und dann bin ich super pünktlich.
- `24:45` Alles klar. Dann, wenn Sie nichts mehr haben, oder?
- `24:47` Haben wir noch irgendwas, wo wir reden müssen?
- `24:49` Brauchen Sie irgendwas sonst?
- `24:51` Und wenn Sie so einen Teil brauchen,
- `24:53` kommen Sie einfach bei mir vorbei.
- `24:54` Können auch zum Herrn Till geben, dem einen schönen Gruß sagen.
- `24:57` Dann kriegen Sie das auch ausgeliehen.
- `25:00` Genau, und auch so eine Exciter-Leiterplatte, wenn Sie die brauchen.
- `25:03` Aber sie können gut mit den Aufnahmen, glaube ich, arbeiten.
- `25:06` Ich glaube, das wäre ganz sinnvoll.
- `25:08` Okay, super.
- `25:09` Dann machen Sie es gut und bis nächste Woche später.
- `25:12` Bis dann. Tschüss.
