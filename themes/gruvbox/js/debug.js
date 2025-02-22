class Debug {
  constructor() {
    this._debugPass = "pes";
    this._init();
  }

  _init() {
    console.log("DEBUG");

    if (!window.theme_utils) {
      window.theme_utils = {};
      window.theme_utils.dirlist = function (path, mode, callback) {
        callback([]);
      };
      window.theme_utils.bind_this = function (context) {
        return context;
      };
    }

    if (!window.greeter_config) {
      window.greeter_config = {
        greeter: {
          debug_mode: true,
        },
        branding: {
          background_images_dir: "",
        },
        layouts: [
          { name: "latam", description: "", short_description: "es" },
          { name: "us", description: "", short_description: "en" },
        ],
      };
    }

    if (!window.lightdm) {
      window.lightdm = {};
    }

    var local_lightdm = {
      default_password: "pes",
      is_authenticated: false,
      authentication_user: null,
      default_session: "awesome",
      can_suspend: true,
      can_hibernate: true,
      can_shutdown: true,
      can_restart: true,
      can_access_battery: true,
      can_access_brightness: true,
      sessions: [
        {
          name: "awesome wm",
          key: "awesome",
        },
        {
          name: "Ubuntu",
          key: "ubuntu",
        },
        {
          name: "i3wm",
          key: "i3",
        },
        {
          name: "bspwm",
          key: "bspwm",
        },
      ],
      users: [
        {
          display_name: "Miyuki Shirogane",
          username: "Arsène",
          image: "./assets/users/Arsene.jpg",
        },
        {
          display_name: "Kaguya Shinomiya",
          username: "Ice princess",
          image: "./assets/users/Ice princess.jpg",
        },
        {
          display_name: "Easper",
          username: "espaiar",
          image: "",
        },
      ],
      languages: [
        {
          name: "American English",
          code: "en_US.utf8",
        },
      ],
      language: "American English",
      layout: { name: "latam", description: "", short_description: "es" },
      authenticate: (username) => {
        console.log(`Starting authentication with user: "${username}"`);
      },
      cancel_authentication: () => {
        console.log(`Authentication cancelled`);
      },
      respond: async (password) => {
        console.log(`Password provided: "${password}"`);
        if (password == this._debugPass) {
          lightdm.is_authenticated = true;
        } else {
          await wait(2000);
        }
        authentication_done();
      },
      start_session: (session) => {
        alert(`Logged with session: "${session}"`);
        location.reload();
      },
      shutdown: () => {
        console.log("System is shutting down...");
        setTimeout(() => location.reload(), 2000);
      },
      restart: () => {
        console.log("System is rebooting...");
        setTimeout(() => location.reload(), 2000);
      },
      hibernate: () => {
        console.log("System is hibernating");
        setTimeout(() => location.reload(), 2000);
      },
      suspend: () => {
        console.log("System is suspending");
        setTimeout(() => location.reload(), 2000);
      },
      batteryData: {
        name: "Battery 0",
        level: 85,
        state: "Discharging",
      },
      brightness: 50,
      brightnessSet: (quantity) => {
        lightdm.brightness = quantity;
      },
      brightnessIncrease: (quantity) => {
        lightdm.brightness += quantity;
        if (lightdm.brightness > 100) lightdm.brightness = 100;
      },
      brightnessDecrease: (quantity) => {
        lightdm.brightness -= quantity;
        if (lightdm.brightness < 0) lightdm.brightness = 0;
      },
    };

    if (lightdm.mock == undefined) {
      window.lightdm = {};
      Object.assign(window.lightdm, local_lightdm);
    } else {
      Object.keys(local_lightdm).forEach((key) => {
        var realKey = `_${key}`;
        lightdm[realKey] = local_lightdm[key];
      });
    }
  }
}
