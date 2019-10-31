#!/usr/bin/env python3
# coding: utf-8

import argparse
import sys
from xml.etree import ElementTree as ET

ROUTES_TPL_TOP = """<?xml version="1.0" encoding="UTF-8"?>

<!-- Generated with SUMO Activity-Based Mobility Generator [https://github.com/lcodeca/SUMOActivityGen] -->

<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    """
ROUTE_TPL_BOTTOM = """</routes>"""


def make_parser(file_name):
    """Yield (depart, person, vehicles) tuples from XML file."""
    stored_vehicles = []
    for _, elem in ET.iterparse(file_name, events=['end']):
        if elem.tag == "vehicle":
            stored_vehicles.append(elem)
        elif elem.tag == "person":
            vehicles, stored_vehicles = stored_vehicles, []
            yield (float(elem.get('depart')), elem, vehicles)


def merge_parsers(parsers):
    """Yield merged streams from multiple parsers sorted by depart time."""
    # TODO: use a heapq instead of enumerate(max)?
    # populate initial values and handle empty parsers
    values = []
    for parser in list(parsers):
        try:
            values.append(next(parser))
        except StopIteration:
            parsers.remove(parser)
    # yield stream merged by person depart time
    while parsers and values:
        parser_nr, content = min(enumerate(values), key=lambda x: x[1][0])
        yield content
        try:
            values[parser_nr] = next(parsers[parser_nr])
        except StopIteration:
            del parsers[parser_nr]
            del values[parser_nr]


def write_results(merged_results, outfile):
    """Write merged results to an XML file."""
    outfile.write(ROUTES_TPL_TOP)
    for _depart, person, vehicles in merged_results:
        for vehicle in vehicles:
            outfile.write(ET.tostring(vehicle, 'unicode'))
            vehicle.clear()
        outfile.write(ET.tostring(person, 'unicode'))
        person.clear()
    outfile.write(ROUTE_TPL_BOTTOM)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('file_names', nargs="+")
    args = parser.parse_args()
    write_results(
        merge_parsers([
            make_parser(file_name) for file_name in args.file_names
        ]),
        args.output
    )

