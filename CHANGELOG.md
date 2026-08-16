## v1.41.0

This is a big release, the biggest one yet actually (again)! The first big headline feature here is the new tag gallery page, where you can search, sort, view, and manage your tags. It's like the tag search in the Admin Panel but on steroids! Perfect for both you as the admin, and for any visitors (in case you host a public instance).  
The second headline feature is actually three features! The first one being tag merging (which you can find in the tag management modal), where you can merge a tag into another, making the merged tag an alias of the other in the process. The second being tag alias management (also in the tag management modal), where you can now finally edit the aliases of your tags! The third and final one being bulk apply buttons for the tag aliases and tag implications, where you can bring your existing media collection up to speed by retroactively applying all of your tag aliases and implications!

Other *very* notable features include the new post navigation buttons (with nice little previews of the media you are about to view), all the new keyboard shortcuts (with a new keybinding editor!), the new algorithm (TF-IDF, for those curious) for finding related posts that is significantly more accurate while also being faster (and is also customizable!!), direct web fetching as a new media upload method, and finally, the AI tag predictor now has support for hardware acceleration (only supporting CUDA for now, though)!

Aside from those new features, two new sorting options have now been added (random and by tag count), and the sorting UI is now more compact than ever! I also went and added a "Back to Album" button for when you are viewing media in an album, so you don't need to use the browser's back button anymore. Building on the album changes, I also made the related media and media hierarchy sections more album-friendly!

As for all the bug fixes and such, there were a lot... The most important two being the completely revamped backup system since it didn't work at all last release (I am really sorry about that..), and "full backup"s were actually NOT full backups. But now they are! You might want to update to this version before making any more backups.  
Some of the smaller fixes include fewer network requests when using the AI tag predictor, fixed downloads for large media, the usual fixed styling inconsistencies and stray hardcoded strings, and many more that are not worth mentioning here.

## v1.40.1

This is by far the largest release in the history of Blombooru (sarcasm), fixing a grand total of two bugs. The first one being that scrolling inside the bulk tag editor modals was completely broken, and the second one being a resource leak that could leave orphaned media cache files lying around.

## v1.40.0

This is the biggest release yet, with the headline feature being custom CSS themes, custom background support, and easier logo customization! I know I know, it sounds like this is a theming-focused release, but no, it is actually much more than that! I've also gone and made it so you can update existing posts with new media!

Other notable, but not headline-worthy features include tag editing and a new bulk media rating editor. The AI tag predictor settings have also been moved to the Admin Panel (where they belong), making them persistent and adding tag blacklisting in the process.

Tag implications now also support wildcards, so you no longer have to create 100 separate implication rules for a single concept or series or whatever! You can now also make the "Popular Tags" section in the sidebar show the most popular related tags *globally*, not just from the page you are viewing. There is now also a dedicated 404 page in case you somehow wander into the unknown in your Blombooru instance!

In case you need to know some basic info about your instance without needing to log in, you can use the all-new instance info endpoint which displays public good-to-know information about your instance. Perfect for those who are creating clients or tools that interact with Blombooru's internal API!

There have been several performance improvements for this release, the notable ones being that the media uploader now is more than twice as fast than the previous version, and that database connections are held for much shorter durations when serving media.

The bug fixes include the usual styling inconsistencies and untranslated strings. But also more notably, media serving for large media files has been fixed, handling for fullscreen videos has been fixed, and a more smaller/more technical bugs.

This release also addresses the first security advisory Blombooru has received, fixing an SSRF and redirect vulnerability in the Booru importer's image proxy endpoint ([CVE-2026-57448](https://github.com/mrblomblo/blombooru/security/advisories/GHSA-5c5w-x8jp-fjqw))!
