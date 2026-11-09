(function () {
  var root = document.documentElement;
  var button = document.getElementById("motion");
  function read() { try { return localStorage.getItem("still") === "1"; } catch (err) { return false; } }
  function save(on) { try { localStorage.setItem("still", on ? "1" : "0"); } catch (err) { /* private window */ } }
  function apply(on) {
    root.classList.toggle("still", on);
    if (button) {
      button.textContent = on ? "Play motion" : "Pause motion";
      button.setAttribute("aria-pressed", String(on));
    }
  }
  apply(read());
  if (button) button.addEventListener("click", function () { var on = !root.classList.contains("still"); apply(on); save(on); });

  var menu = document.querySelector(".menu");
  if (menu) {
    document.addEventListener("click", function (ev) { if (menu.open && !menu.contains(ev.target)) menu.open = false; });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && menu.open) { menu.open = false; menu.querySelector("summary").focus(); }
    });
  }
})();
