/* Shared behaviour for the Mancherikalam shop pages.

   Deliberately small and ES5: these pages are read on low-end Android
   phones over 4G, and everything here is progressive enhancement. With
   JavaScript off the pages still read correctly in both languages —
   the only thing lost is the prefilled WhatsApp text, and those links
   fall back to the "Visit us" section, which carries the phone number
   and address as plain text.

   Per-page details (WhatsApp number, phone, map URLs, the prefilled
   greetings) live in one window.PAGE object at the bottom of each page.
   Visible copy lives in the HTML so that crawlers and no-JS visitors
   see it. */

(function () {
  "use strict";

  var root = document.documentElement;
  var PAGE = window.PAGE || {};
  var LANG_KEY = "mk-lang";

  /* ---- language ---- */

  /* The visual swap is pure CSS keyed off data-lang; this only flips the
     attribute, keeps the buttons' aria-pressed honest, and re-renders the
     WhatsApp greeting in the chosen language. */

  function currentLang() {
    return root.getAttribute("data-lang") === "ml" ? "ml" : "en";
  }

  function setLang(lang) {
    lang = lang === "ml" ? "ml" : "en";
    root.setAttribute("data-lang", lang);

    langButtons.forEach(function (button) {
      var pressed = button.getAttribute("data-lang-set") === lang;
      button.setAttribute("aria-pressed", String(pressed));
    });

    try {
      window.localStorage.setItem(LANG_KEY, lang);
    } catch (error) {
      /* Private mode, or storage disabled. The choice just won't persist. */
    }

    buildActionLinks();
  }

  var langButtons = Array.prototype.slice.call(
    document.querySelectorAll("[data-lang-set]")
  );

  langButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      setLang(button.getAttribute("data-lang-set"));
    });
  });

  /* ---- action links ---- */

  /* WhatsApp, call and directions links are built from window.PAGE so each
     number lives in exactly one place per page, and so the prefilled message
     follows the reader's language. */

  function waHref(key) {
    var number = String(PAGE.whatsapp || "");
    var group = PAGE.messages && PAGE.messages[key];
    var text = (group && (group[currentLang()] || group.en)) || "";
    return "https://wa.me/91" + number + "?text=" + encodeURIComponent(text);
  }

  function telHref() {
    return "tel:" + String(PAGE.phone || "").replace(/\s+/g, "");
  }

  function buildActionLinks() {
    each("[data-wa]", function (link) {
      apply(link, waHref(link.getAttribute("data-wa")), PAGE.whatsapp);
    });

    each("[data-tel]", function (link) {
      apply(link, telHref(), PAGE.phone);
      var slot = link.querySelector("[data-tel-text]");
      if (slot && PAGE.phone) slot.textContent = PAGE.phone;
    });

    each("[data-directions]", function (link) {
      var url = (PAGE.maps && PAGE.maps.directions) || "";
      apply(link, url, url);
    });

    /* Plain links whose href is itself a token (the Facebook page, the
       WhatsApp group) get the same treatment until the deploy fills them. */
    each("[data-link]", function (link) {
      var url = link.getAttribute("href") || "";
      apply(link, url, url);
    });
  }

  function each(selector, fn) {
    Array.prototype.slice.call(document.querySelectorAll(selector)).forEach(fn);
  }

  /* ---- placeholder guard ---- */

  /* Until a real number or URL is filled in, the value still contains a
     [BRACKETED] token. Rather than leave a dead tap, flag the control so it
     is visibly unfinished. This switches itself off once window.PAGE holds
     real values — no cleanup needed. */

  function apply(link, href, source) {
    var unfilled = !source || String(source).indexOf("[") !== -1;

    if (unfilled) {
      link.setAttribute("data-placeholder", "");
      link.setAttribute("aria-disabled", "true");
      return;
    }

    link.removeAttribute("data-placeholder");
    link.removeAttribute("aria-disabled");
    link.setAttribute("href", href);
  }

  document.addEventListener("click", function (event) {
    var blocked = event.target.closest
      ? event.target.closest("[aria-disabled='true']")
      : null;
    if (blocked) event.preventDefault();
  });

  /* ---- mobile nav ---- */

  var navToggle = document.getElementById("nav-toggle");
  var nav = document.getElementById("nav");

  if (navToggle && nav) {
    var closeNav = function () {
      navToggle.setAttribute("aria-expanded", "false");
      nav.classList.remove("is-open");
    };

    navToggle.addEventListener("click", function () {
      var isOpen = nav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(isOpen));
    });

    nav.addEventListener("click", function (event) {
      if (event.target.tagName === "A") closeNav();
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeNav();
    });
  }

  /* ---- map ---- */

  /* Click to load, not just loading="lazy". Google's embed is a third party;
     not requesting it until someone asks for the map keeps the promise that
     the page sets no cookies and calls nothing out on its own. */

  var mapButton = document.querySelector("[data-map]");

  if (mapButton) {
    var embed = (PAGE.maps && PAGE.maps.embed) || "";

    if (!embed || embed.indexOf("[") !== -1) {
      mapButton.setAttribute("data-placeholder", "");
      mapButton.setAttribute("aria-disabled", "true");
      mapButton.disabled = true;
    } else {
      mapButton.addEventListener("click", function () {
        var frame = document.createElement("iframe");
        frame.src = embed;
        frame.title = mapButton.getAttribute("data-map-title") || "Map";
        frame.width = "600";
        frame.height = "450";
        frame.loading = "lazy";
        frame.referrerPolicy = "no-referrer-when-downgrade";
        frame.setAttribute("allowfullscreen", "");
        mapButton.parentNode.replaceChild(frame, mapButton);
      });
    }
  }

  /* ---- gallery lightbox ---- */

  /* Each thumbnail is a plain link to the full-size photo, so without
     JavaScript (or without <dialog> support) a tap simply opens the image.
     Here the click is upgraded to an in-page viewer that closes on Esc,
     on the close button, or on a tap outside the photo. */

  var gallery = document.querySelector("[data-gallery]");

  if (gallery && typeof HTMLDialogElement === "function") {
    var dialog = document.createElement("dialog");
    dialog.className = "lightbox";
    dialog.setAttribute("aria-label", "Photo");

    var closeButton = document.createElement("button");
    closeButton.className = "lightbox-close";
    closeButton.type = "button";
    closeButton.setAttribute("aria-label", "Close");
    closeButton.textContent = "×";

    var photo = document.createElement("img");
    photo.width = 720;
    photo.height = 1280;
    photo.alt = "";

    var caption = document.createElement("p");

    dialog.appendChild(closeButton);
    dialog.appendChild(photo);
    dialog.appendChild(caption);
    document.body.appendChild(dialog);

    gallery.addEventListener("click", function (event) {
      var link = event.target.closest ? event.target.closest("a") : null;
      if (!link) return;
      event.preventDefault();

      var thumb = link.querySelector("img");
      photo.src = link.getAttribute("href");
      photo.alt = thumb ? thumb.alt : "";
      caption.textContent = photo.alt;
      dialog.showModal();
    });

    closeButton.addEventListener("click", function () {
      dialog.close();
    });

    /* A click on the backdrop lands on the dialog element itself. */
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) dialog.close();
    });
  }

  /* ---- footer year ---- */

  var year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();

  /* ---- init ---- */

  /* data-lang is already set by the inline script in <head> (before first
     paint, so the bilingual order never visibly flips). Re-running setLang
     syncs the buttons and builds the action links. */

  setLang(currentLang());
})();
