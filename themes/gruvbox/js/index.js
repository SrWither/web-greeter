
form = document.querySelector("#form > form")

function getArrayForm(inputs) {
	if (!inputs) return false
	var data = {}
	inputs.forEach((x) => {
		data[x.name] = x.value
	})
	return data
}

async function wait(ms) {
  return new Promise( resolve => {
    setTimeout(() => {
      resolve()
    }, ms)
  })
}

async function initGreeter() {
  if (lightdm.authentication_complete) {
    lightdm.authentication_complete.connect(() => authentication_done())
  }

  if (greeter_config.greeter.debug_mode) {
    debug = new Debug()
  }

  accounts = new Accounts()

  sessions = new Sessions()

  authenticate = new Authenticate()

  power = new Power()

  battery = new Battery()
  
  brightness = new Brightness()

}

const notGreeter = false

if (notGreeter) {
  debug = new Debug()
  initGreeter()
} else {
  window.addEventListener("GreeterReady", initGreeter)
}
