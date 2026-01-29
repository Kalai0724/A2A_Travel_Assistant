// ...existing code...
import { LitElement, html, css } from "lit";
import { property } from "lit/decorators.js";
import { customElement } from "lit/decorators.js";

@customElement("weather-dashboard")
export class WeatherDashboard extends LitElement {
  @property({ type: Object }) weather: any = {};
  @property({ type: String }) city: string = "";
  @property({ type: String }) search: string = "";
  @property({ type: Number }) expandedDay: number | null = null;

  private daysGridRef: HTMLElement | null = null;
  private sliderValue: number = 0;
  private sliderMax: number = 0;

  static styles = css`
    .day-card {
      background: #fff;
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 1px 4px #0001;
      cursor: pointer;
      transition: box-shadow 0.2s;
      width: 100%;
      box-sizing: border-box;
      margin-bottom: 16px;
    }
      gap: 8px;
      margin-bottom: 8px;
    }
    .today-card {
      background: #f5f7fa;
      border-radius: 16px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      align-items: center;
      box-shadow: 0 2px 8px #0001;
      gap: 8px;
    }
    .today-main {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .today-temp {
      font-size: 3rem;
      font-weight: bold;
    }
    .today-details {
      display: flex;
      gap: 16px;
      font-size: 1.1rem;
      color: #555;
    }
    .hourly-scroll {
      display: flex;
      overflow-x: auto;
      gap: 12px;
      padding-bottom: 8px;
    }
    .hour-card {
      min-width: 70px;
      background: #fff;
      border-radius: 10px;
      padding: 8px 6px;
      text-align: center;
      box-shadow: 0 1px 4px #0001;
      font-size: 0.95rem;
    }
    .days-grid {
      display: flex;
      flex-direction: column;
      flex-wrap: nowrap;
      gap: 24px;
      width: 100%;
      overflow-x: auto;
      padding-bottom: 1rem;
      box-sizing: border-box;
      scrollbar-color:#000000 #0c0505;
      scrollbar-width: thin;
    }

    .days-grid::-webkit-scrollbar {
      height: 12px;
      background: #0c0505;
      border-radius: 6px;
    }
    .days-grid::-webkit-scrollbar-thumb {
      background: #000000;
      border-radius: 6px;
    }
    .days-grid {
      display: flex;
      flex-direction: column;
      gap: 24px;
      width: 100%;
      box-sizing: border-box;
      /* Remove horizontal scrolling for vertical layout */
    }
    .day-card:hover {
      box-shadow: 0 4px 16px #0002;
    }
    .details {
      margin-top: 10px;
      font-size: 0.98rem;
      color: #444;
      background: #f8fafc;
      border-radius: 8px;
      padding: 10px 8px;
    }
    .chart {
      background: #fff;
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 1px 4px #0001;
      min-height: 120px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.1rem;
      color: #888;
    }
  `;

  getIcon(condition: string) {
    if (/clear/i.test(condition)) return "";
    if (/rain/i.test(condition)) return "🌧️";
    if (/cloud/i.test(condition)) return "☁️";
    if (/thunder/i.test(condition)) return "⛈️";
    if (/mist|fog/i.test(condition)) return "🌫️";
    return "❓";
  }

  handleSearch(e: Event) {
    e.preventDefault();
    this.dispatchEvent(new CustomEvent("search", { detail: this.search }));
  }

  handleDaysGridScroll(event: Event): void {
    console.log('Days grid scrolled', event);
    // Add logic to handle scroll event
  }

  handleSliderInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.sliderValue = Number(input.value);
    console.log('Slider value changed to', this.sliderValue);
    // Add logic to handle slider input
  }

  render() {
    const today = this.weather?.current || {};
    const hourly = this.weather?.hourly || [];
    const daily = this.weather?.daily || [];
    return html`
      <div class="dashboard">
        <form class="search-bar" @submit=${this.handleSearch}>
          <input
            type="text"
            .value=${this.search}
            @input=${(e: any) => (this.search = e.target.value)}
            placeholder="Search city..."
          />
          <button type="submit">Search</button>
        </form>
        <div class="today-card">
          <div class="today-main">
            <span style="font-size:2.5rem;">${this.getIcon(today.condition || "")}</span>
            <div>
              <div class="today-temp">${today.temp ?? "--"}°</div>
              <div>${this.city}</div>
            </div>
          </div>
          <div class="today-details">
            <span>Feels: ${today.feels_like ?? "--"}°</span>
            <span>💧 ${today.humidity ?? "--"}%</span>
            <span>💨 ${today.wind ?? "--"} km/h</span>
          </div>
        </div>
        <div class="hourly-scroll">
          ${hourly.map(
            (h: any) => html`
              <div class="hour-card">
                <div>${h.time}</div>
                <div style="font-size:1.5rem;">${this.getIcon(h.condition)}</div>
                <div>${h.temp}°</div>
              </div>
            `
          )}
        </div>
        <div class="chart">[Temperature Trend Chart Placeholder]</div>
        <div class="days-grid" 
          ${ref => { this.daysGridRef = ref as HTMLElement; }}
          @scroll=${this.handleDaysGridScroll.bind(this)}>
          ${daily.map(
            (d: any, i: number) => html`
              <div class="day-card" @click=${() => (this.expandedDay = this.expandedDay === i ? null : i)}>
                <div style="display:flex;align-items:center;gap:8px;">
                  <span style="font-size:1.3rem;">${this.getIcon(d.condition)}</span>
                  <span>${d.day}</span>
                  <span>${d.temp_min}° / ${d.temp_max}°</span>
                </div>
                <div>Rain: ${d.rain_chance ?? "--"}% | Precip: ${d.precip ?? "--"}mm</div>
                ${this.expandedDay === i
                  ? html`<div class="details">
                      <div>Wind: ${d.wind ?? "--"} km/h</div>
                      <div>Humidity: ${d.humidity ?? "--"}%</div>
                      <div>UV: ${d.uv ?? "--"}</div>
                      <div>Sunrise: ${d.sunrise ?? "--"}</div>
                      <div>Sunset: ${d.sunset ?? "--"}</div>
                    </div>`
                  : ""}
              </div>
            `
          )}
        </div>
        ${this.sliderMax > 0 ? html`
          <input
            type="range"
            min="0"
            max="${this.sliderMax}"
            .value="${String(this.sliderValue)}"
            @input=${this.handleSliderInput.bind(this)}
            style="width: 60%; margin: 2rem auto 0 auto; display: block;"
          />
        ` : ''}
      </div>
    `;
  }
}

// Usage: <weather-dashboard .weather=${weatherData} city="London"></weather-dashboard>
// Listen for "search" event to update city
