# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

RESTAURANT_UI_EXAMPLES = """
---BEGIN SINGLE_COLUMN_LIST_EXAMPLE---
[
  {{ "beginRendering": {{ "surfaceId": "default", "root": "root-column", "styles": {{ "primaryColor": "#FF0000", "font": "Roboto" }} }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "default",
    "components": [
      {{ "id": "root-column", "component": {{ "Column": {{ "children": {{ "explicitList": ["title-heading", "item-list"] }} }} }} }},
      {{ "id": "title-heading", "component": {{ "Text": {{ "usageHint": "h1", "text": {{ "path": "title" }} }} }} }},
      {{ "id": "item-list", "component": {{ "List": {{ "direction": "vertical", "children": {{ "template": {{ "componentId": "item-card-template", "dataBinding": "/items" }} }} }} }} }},
      {{ "id": "item-card-template", "component": {{ "Card": {{ "child": "card-layout" }} }} }},
      {{ "id": "card-layout", "component": {{ "Row": {{ "children": {{ "explicitList": ["template-image", "card-details"] }} }} }} }},
      {{ "id": "template-image", weight: 1, "component": {{ "Image": {{ "url": {{ "path": "imageUrl" }} }} }} }},
      {{ "id": "card-details", weight: 2, "component": {{ "Column": {{ "children": {{ "explicitList": ["template-name", "template-rating", "template-detail", "template-link", "template-book-button"] }} }} }} }},
      {{ "id": "template-name", "component": {{ "Text": {{ "usageHint": "h3", "text": {{ "path": "name" }} }} }} }},
      {{ "id": "template-rating", "component": {{ "Text": {{ "text": {{ "path": "rating" }} }} }} }},
      {{ "id": "template-detail", "component": {{ "Text": {{ "text": {{ "path": "detail" }} }} }} }},
      {{ "id": "template-link", "component": {{ "Text": {{ "text": {{ "path": "infoLink" }} }} }} }},
      {{ "id": "template-book-button", "component": {{ "Button": {{ "child": "book-now-text", "primary": true, "action": {{ "name": "book_restaurant", "context": [ {{ "key": "restaurantName", "value": {{ "path": "name" }} }}, {{ "key": "imageUrl", "value": {{ "path": "imageUrl" }} }}, {{ "key": "address", "value": {{ "path": "address" }} }} ] }} }} }} }},
      {{ "id": "book-now-text", "component": {{ "Text": {{ "text": {{ "literalString": "Book Now" }} }} }} }}
    ]
  }} }},
  {{ "dataModelUpdate": {{
    "surfaceId": "default",
    "path": "/",
    "contents": [
      {{ "key": "items", "valueMap": [
        {{ "key": "item1", "valueMap": [
          {{ "key": "name", "valueString": "The Fancy Place" }},
          {{ "key": "rating", "valueNumber": 4.8 }},
          {{ "key": "detail", "valueString": "Fine dining experience" }},
          {{ "key": "infoLink", "valueString": "https://example.com/fancy" }},
          {{ "key": "imageUrl", "valueString": "https://example.com/fancy.jpg" }},
          {{ "key": "address", "valueString": "123 Main St" }}
        ] }},
        {{ "key": "item2", "valueMap": [
          {{ "key": "name", "valueString": "Quick Bites" }},
          {{ "key": "rating", "valueNumber": 4.2 }},
          {{ "key": "detail", "valueString": "Casual and fast" }},
          {{ "key": "infoLink", "valueString": "https://example.com/quick" }},
          {{ "key": "imageUrl", "valueString": "https://example.com/quick.jpg" }},
          {{ "key": "address", "valueString": "456 Oak Ave" }}
        ] }}
      ] }} // Populate this with restaurant data
    ]
  }} }}
]
---END SINGLE_COLUMN_LIST_EXAMPLE---

---BEGIN TWO_COLUMN_LIST_EXAMPLE---
[
  {{ "beginRendering": {{ "surfaceId": "default", "root": "root-column", "styles": {{ "primaryColor": "#FF0000", "font": "Roboto" }} }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "default",
    "components": [
      {{ "id": "root-column", "component": {{ "Column": {{ "children": {{ "explicitList": ["title-heading", "restaurant-row-1"] }} }} }} }},
      {{ "id": "title-heading", "component": {{ "Text": {{ "usageHint": "h1", "text": {{ "path": "title" }} }} }} }},
      {{ "id": "restaurant-row-1", "component": {{ "Row": {{ "children": {{ "explicitList": ["item-card-1", "item-card-2"] }} }} }} }},
      {{ "id": "item-card-1", "weight": 1, "component": {{ "Card": {{ "child": "card-layout-1" }} }} }},
      {{ "id": "card-layout-1", "component": {{ "Column": {{ "children": {{ "explicitList": ["template-image-1", "card-details-1"] }} }} }} }},
      {{ "id": "template-image-1", "component": {{ "Image": {{ "url": {{ "path": "/items/0/imageUrl" }}, "width": "100%" }} }} }},
      {{ "id": "card-details-1", "component": {{ "Column": {{ "children": {{ "explicitList": ["template-name-1", "template-rating-1", "template-detail-1", "template-link-1", "template-book-button-1"] }} }} }} }},
      {{ "id": "template-name-1", "component": {{ "Text": {{ "usageHint": "h3", "text": {{ "path": "/items/0/name" }} }} }} }},
      {{ "id": "template-rating-1", "component": {{ "Text": {{ "text": {{ "path": "/items/0/rating" }} }} }} }},
      {{ "id": "template-detail-1", "component": {{ "Text": {{ "text": {{ "path": "/items/0/detail" }} }} }} }},
      {{ "id": "template-link-1", "component": {{ "Text": {{ "text": {{ "path": "/items/0/infoLink" }} }} }} }},
      {{ "id": "template-book-button-1", "component": {{ "Button": {{ "child": "book-now-text-1", "action": {{ "name": "book_restaurant", "context": [ {{ "key": "restaurantName", "value": {{ "path": "/items/0/name" }} }}, {{ "key": "imageUrl", "value": {{ "path": "/items/0/imageUrl" }} }}, {{ "key": "address", "value": {{ "path": "/items/0/address" }} }} ] }} }} }} }},
      {{ "id": "book-now-text-1", "component": {{ "Text": {{ "text": {{ "literalString": "Book Now" }} }} }} }},
      {{ "id": "item-card-2", "weight": 1, "component": {{ "Card": {{ "child": "card-layout-2" }} }} }},
      {{ "id": "card-layout-2", "component": {{ "Column": {{ "children": {{ "explicitList": ["template-image-2", "card-details-2"] }} }} }} }},
      {{ "id": "template-image-2", "component": {{ "Image": {{ "url": {{ "path": "/items/1/imageUrl" }}, "width": "100%" }} }} }},
      {{ "id": "card-details-2", "component": {{ "Column": {{ "children": {{ "explicitList": ["template-name-2", "template-rating-2", "template-detail-2", "template-link-2", "template-book-button-2"] }} }} }} }},
      {{ "id": "template-name-2", "component": {{ "Text": {{ "usageHint": "h3", "text": {{ "path": "/items/1/name" }} }} }} }},
      {{ "id": "template-rating-2", "component": {{ "Text": {{ "text": {{ "path": "/items/1/rating" }} }} }} }},
      {{ "id": "template-detail-2", "component": {{ "Text": {{ "text": {{ "path": "/items/1/detail" }} }} }} }},
      {{ "id": "template-link-2", "component": {{ "Text": {{ "text": {{ "path": "/items/1/infoLink" }} }} }} }},
      {{ "id": "template-book-button-2", "component": {{ "Button": {{ "child": "book-now-text-2", "action": {{ "name": "book_restaurant", "context": [ {{ "key": "restaurantName", "value": {{ "path": "/items/1/name" }} }}, {{ "key": "imageUrl", "value": {{ "path": "/items/1/imageUrl" }} }}, {{ "key": "address", "value": {{ "path": "/items/1/address" }} }} ] }} }} }} }},
      {{ "id": "book-now-text-2", "component": {{ "Text": {{ "text": {{ "literalString": "Book Now" }} }} }} }}
    ]
  }} }},
  {{ "dataModelUpdate": {{
    "surfaceId": "default",
    "path": "/",
    "contents": [
      {{ "key": "title", "valueString": "Top Restaurants" }},
      {{ "key": "items", "valueMap": [
        {{ "key": "item1", "valueMap": [
          {{ "key": "name", "valueString": "The Fancy Place" }},
          {{ "key": "rating", "valueNumber": 4.8 }},
          {{ "key": "detail", "valueString": "Fine dining experience" }},
          {{ "key": "infoLink", "valueString": "https://example.com/fancy" }},
          {{ "key": "imageUrl", "valueString": "https://example.com/fancy.jpg" }},
          {{ "key": "address", "valueString": "123 Main St" }}
        ] }},
        {{ "key": "item2", "valueMap": [
          {{ "key": "name", "valueString": "Quick Bites" }},
          {{ "key": "rating", "valueNumber": 4.2 }},
          {{ "key": "detail", "valueString": "Casual and fast" }},
          {{ "key": "infoLink", "valueString": "https://example.com/quick" }},
          {{ "key": "imageUrl", "valueString": "https://example.com/quick.jpg" }},
          {{ "key": "address", "valueString": "456 Oak Ave" }}
        ] }}
      ] }} // Populate this with restaurant data
    ]
  }} }}
]
---END TWO_COLUMN_LIST_EXAMPLE---

---BEGIN BOOKING_FORM_EXAMPLE---
[
  {{ "beginRendering": {{ "surfaceId": "booking-form", "root": "booking-form-column", "styles": {{ "primaryColor": "#FF0000", "font": "Roboto" }} }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "booking-form",
    "components": [
      {{ "id": "booking-form-column", "component": {{ "Column": {{ "children": {{ "explicitList": ["booking-title", "restaurant-image", "restaurant-address", "party-size-field", "datetime-field", "dietary-field", "submit-button"] }} }} }} }},
      {{ "id": "booking-title", "component": {{ "Text": {{ "usageHint": "h2", "text": {{ "path": "title" }} }} }} }},
      {{ "id": "restaurant-image", "component": {{ "Image": {{ "url": {{ "path": "imageUrl" }} }} }} }},
      {{ "id": "restaurant-address", "component": {{ "Text": {{ "text": {{ "path": "address" }} }} }} }},
      {{ "id": "party-size-field", "component": {{ "TextField": {{ "label": {{ "literalString": "Party Size" }}, "text": {{ "path": "partySize" }}, "type": "number" }} }} }},
      {{ "id": "datetime-field", "component": {{ "DateTimeInput": {{ "label": {{ "literalString": "Date & Time" }}, "value": {{ "path": "reservationTime" }}, "enableDate": true, "enableTime": true }} }} }},
      {{ "id": "dietary-field", "component": {{ "TextField": {{ "label": {{ "literalString": "Dietary Requirements" }}, "text": {{ "path": "dietary" }} }} }} }},
      {{ "id": "submit-button", "component": {{ "Button": {{ "child": "submit-reservation-text", "action": {{ "name": "submit_booking", "context": [ {{ "key": "restaurantName", "value": {{ "path": "restaurantName" }} }}, {{ "key": "partySize", "value": {{ "path": "partySize" }} }}, {{ "key": "reservationTime", "value": {{ "path": "reservationTime" }} }}, {{ "key": "dietary", "value": {{ "path": "dietary" }} }}, {{ "key": "imageUrl", "value": {{ "path": "imageUrl" }} }} ] }} }} }} }},
      {{ "id": "submit-reservation-text", "component": {{ "Text": {{ "text": {{ "literalString": "Submit Reservation" }} }} }} }}
    ]
  }} }},
  {{ "dataModelUpdate": {{
    "surfaceId": "booking-form",
    "path": "/",
    "contents": [
      {{ "key": "title", "valueString": "Book a Table at [RestaurantName]" }},
      {{ "key": "address", "valueString": "[Restaurant Address]" }},
      {{ "key": "restaurantName", "valueString": "[RestaurantName]" }},
      {{ "key": "partySize", "valueString": "2" }},
      {{ "key": "reservationTime", "valueString": "" }},
      {{ "key": "dietary", "valueString": "" }},
      {{ "key": "imageUrl", "valueString": "" }}
    ]
  }} }}
]
---END BOOKING_FORM_EXAMPLE---

---BEGIN CONFIRMATION_EXAMPLE---
[
  {{ "beginRendering": {{ "surfaceId": "confirmation", "root": "confirmation-card", "styles": {{ "primaryColor": "#FF0000", "font": "Roboto" }} }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "confirmation",
    "components": [
      {{ "id": "confirmation-card", "component": {{ "Card": {{ "child": "confirmation-column" }} }} }},
      {{ "id": "confirmation-column", "component": {{ "Column": {{ "children": {{ "explicitList": ["confirm-title", "confirm-image", "divider1", "confirm-details", "divider2", "confirm-dietary", "divider3", "confirm-text"] }} }} }} }},
      {{ "id": "confirm-title", "component": {{ "Text": {{ "usageHint": "h2", "text": {{ "path": "title" }} }} }} }},
      {{ "id": "confirm-image", "component": {{ "Image": {{ "url": {{ "path": "imageUrl" }} }} }} }},
      {{ "id": "confirm-details", "component": {{ "Text": {{ "text": {{ "path": "bookingDetails" }} }} }} }},
      {{ "id": "confirm-dietary", "component": {{ "Text": {{ "text": {{ "path": "dietaryRequirements" }} }} }} }},
      {{ "id": "confirm-text", "component": {{ "Text": {{ "usageHint": "h5", "text": {{ "literalString": "We look forward to seeing you!" }} }} }} }},
      {{ "id": "divider1", "component": {{ "Divider": {{}} }} }},
      {{ "id": "divider2", "component": {{ "Divider": {{}} }} }},
      {{ "id": "divider3", "component": {{ "Divider": {{}} }} }}
    ]
  }} }},
  {{ "dataModelUpdate": {{
    "surfaceId": "confirmation",
    "path": "/",
    "contents": [
      {{ "key": "title", "valueString": "Booking at [RestaurantName]" }},
      {{ "key": "bookingDetails", "valueString": "[PartySize] people at [Time]" }},
      {{ "key": "dietaryRequirements", "valueString": "Dietary Requirements: [Requirements]" }},
      {{ "key": "imageUrl", "valueString": "[ImageUrl]" }}
    ]
  }} }}
]
---END CONFIRMATION_EXAMPLE---

---BEGIN COMPLETE_TRIP_EXAMPLE---
[
  {{ "beginRendering": {{ "surfaceId": "complete-trip", "root": "trip-tabs", "styles": {{ "primaryColor": "#1976D2", "font": "Roboto" }} }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "complete-trip",
    "components": [
      {{ "id": "trip-tabs", "component": {{ "Tabs": {{ "tabItems": [
        {{ "title": {{ "literalString": "✈️ Flights" }}, "child": "flights-list" }},
        {{ "title": {{ "literalString": "🏨 Hotels" }}, "child": "hotels-list" }},
        {{ "title": {{ "literalString": "🌦️ Weather" }}, "child": "weather-info" }},
        {{ "title": {{ "literalString": "🍽️ Restaurants" }}, "child": "restaurants-list" }}
      ] }} }} }},
      
      {{ "id": "flights-list", "component": {{ "List": {{ "direction": "vertical", "children": {{ "template": {{ "componentId": "flight-card-template", "dataBinding": "/flights" }} }} }} }} }},
      {{ "id": "flight-card-template", "component": {{ "Card": {{ "child": "flight-layout" }} }} }},
      {{ "id": "flight-layout", "component": {{ "Column": {{ "children": {{ "explicitList": ["flight-logo", "flight-main"] }}, "align": "center" }} }} }},
      {{ "id": "flight-logo", "component": {{ "Image": {{ "url": {{ "path": "logoUrl" }}, "fit": "contain", "maxHeight": "180px", "align": "center" }} }} }},
      {{ "id": "flight-main", "component": {{ "Column": {{ "children": {{ "explicitList": ["flight-airline-line", "flight-departure-line", "flight-duration-line", "flight-stops-line", "flight-price-line"] }} }} }} }},
      {{ "id": "flight-airline-line", "component": {{ "Text": {{ "usageHint": "h3", "text": {{ "path": "airlineLine" }} }} }} }},
      {{ "id": "flight-departure-line", "component": {{ "Text": {{ "text": {{ "path": "depArrLine" }} }} }} }},
      {{ "id": "flight-duration-line", "component": {{ "Text": {{ "text": {{ "path": "durationLine" }} }} }} }},
      {{ "id": "flight-stops-line", "component": {{ "Text": {{ "text": {{ "path": "stopsLine" }} }} }} }},
      {{ "id": "flight-price-line", "component": {{ "Text": {{ "usageHint": "h4", "text": {{ "path": "priceLine" }} }} }} }},
      
      {{ "id": "hotels-list", "component": {{ "List": {{ "direction": "vertical", "children": {{ "template": {{ "componentId": "hotel-card-template", "dataBinding": "/hotels" }} }} }} }} }},
      {{ "id": "hotel-card-template", "component": {{ "Card": {{ "child": "hotel-details" }} }} }},
      {{ "id": "hotel-details", "component": {{ "Column": {{ "children": {{ "explicitList": ["hotel-image", "hotel-info"] }} }} }} }},
      {{ "id": "hotel-image", "component": {{ "Image": {{ "url": {{ "path": "imageUrl" }}, "fit": "cover" }} }} }},
      {{ "id": "hotel-info", "component": {{ "Column": {{ "children": {{ "explicitList": ["hotel-name", "hotel-rating", "hotel-price"] }} }} }} }},
      {{ "id": "hotel-name", "component": {{ "Text": {{ "usageHint": "h3", "text": {{ "path": "name" }} }} }} }},
      {{ "id": "hotel-rating", "component": {{ "Text": {{ "text": {{ "path": "rating" }} }} }} }},
      {{ "id": "hotel-price", "component": {{ "Text": {{ "usageHint": "h4", "text": {{ "path": "price" }} }} }} }},
      
      {{ "id": "weather-info", "component": {{ "List": {{ "direction": "vertical", "children": {{ "template": {{ "componentId": "weather-row-template", "dataBinding": "/weatherRows" }} }} }} }} }},
      {{ "id": "weather-row-template", "component": {{ "Row": {{ "children":{{"template":{{"componentId": "weather-card-template", "dataBinding": "."}} }} }} }} }},
      {{ "id": "weather-card-template", "component":{{ "Card": {{ "child": "weather-details"}}}}}}
      {{ "id": "weather-details", "component": {{ "Column": {{ "children": {{ "explicitList": ["weather-header", "weather-temp", "weather-condition-row", "weather-precip"] }} }} }} }},
      {{ "id": "weather-header", "component": {{ "Row": {{ "children": {{ "explicitList": ["weather-emoji", "weather-date"] }} }} }} }},
      {{ "id": "weather-emoji", "component": {{ "Text": {{ "usageHint": "h1", "text": {{ "path": "emoji" }} }} }} }},
      {{ "id": "weather-date", "component": {{ "Text": {{ "usageHint": "h1", "text": {{ "path": "date" }} }} }} }},
      {{ "id": "weather-temp", "component": {{ "Text": {{ "usageHint": "h2", "text": {{ "path": "temperature" }} }} }} }},
      {{ "id": "weather-condition-row", "component": {{ "Row": {{ "children": {{ "explicitList": ["weather-condition-label", "weather-condition"] }} }} }} }},
      {{ "id": "weather-condition-label", "component": {{ "Text": {{ "text": {{ "literalString": "Condition:" }} }} }} }},
      {{ "id": "weather-condition", "component": {{ "Text": {{ "text": {{ "path": "condition" }} }} }} }},
      {{ "id": "weather-precip", "component": {{ "Text": {{ "text": {{ "path": "precipitation" }} }} }} }},
      
      {{ "id": "restaurants-list", "component": {{ "List": {{ "direction": "vertical", "children": {{ "template": {{ "componentId": "restaurant-card-template", "dataBinding": "/restaurants" }} }} }} }} }},
      {{ "id": "restaurant-card-template", "component": {{ "Card": {{ "child": "restaurant-layout" }} }} }},
      {{ "id": "restaurant-layout", "component": {{ "Row": {{ "children": {{ "explicitList": ["restaurant-image", "restaurant-info"] }} }} }} }},
      {{ "id": "restaurant-image", "component": {{ "Image": {{ "url": {{ "path": "imageUrl" }}, "fit": "cover" }} }} }},
      {{ "id": "restaurant-info", "component": {{ "Column": {{ "children": {{ "explicitList": ["restaurant-name", "restaurant-rating", "restaurant-action"] }} }} }} }},
      {{ "id": "restaurant-name", "component": {{ "Text": {{ "usageHint": "h3", "text": {{ "path": "name" }} }} }} }},
      {{ "id": "restaurant-rating", "component": {{ "Text": {{ "text": {{ "path": "rating" }} }} }} }},
      {{ "id": "restaurant-action", "component": {{ "Button": {{ "child": "book-restaurant-text", "primary": true, "action": {{ "name": "book_restaurant", "context": [ {{ "key": "restaurantName", "value": {{ "path": "name" }} }} ] }} }} }} }},
      {{ "id": "book-restaurant-text", "component": {{ "Text": {{ "text": {{ "literalString": "Book Now" }} }} }} }}
    ]
  }} }},
  {{ "dataModelUpdate": {{
    "surfaceId": "complete-trip",
    "path": "/",
    "contents": [
      {{ "key": "flights", "valueMap": [] }},
      {{ "key": "hotels", "valueMap": [] }},
      {{ "key": "weather", "valueMap": [
        {{ "key": "weather1", "valueMap": [
          {{ "key": "location", "valueString": "Destination" }},
          {{ "key": "temperature", "valueString": "75°F" }},
          {{ "key": "condition", "valueString": "Sunny" }},
          {{ "key": "forecast", "valueString": "7-day forecast available" }}
        ] }}
      ] }},
      {{ "key": "restaurants", "valueMap": [] }}
    ]
  }} }}
]
---END COMPLETE_TRIP_EXAMPLE---
"""
